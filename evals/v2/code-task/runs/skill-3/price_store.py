"""Append-only price revisions (tier T2: production, concurrent callers, audit columns).

One guarded write path: set_price() validates, locks the product, re-checks the
expected revision, supersedes the current row and inserts revision + 1, all in
one transaction that commits on success and rolls back on any failure.
"""

import logging
from decimal import Decimal, InvalidOperation

logger = logging.getLogger(__name__)

_ORIGINS = frozenset({"ui", "agent_confirmed", "import", "backfill"})  # mirrors the DB CHECK
_STEP = Decimal("0.0001")  # numeric(14,4): 4 decimals
_MAX = Decimal(10) ** 10  # numeric(14,4): 10 integer digits


class StaleRevision(Exception):
    """expected_revision does not match the product's current revision (map to HTTP 409)."""


def _parse_price(value) -> Decimal:
    # Exact numbers only: floats are refused rather than guessed at; the DB would
    # otherwise round extra decimals silently.
    if isinstance(value, bool) or isinstance(value, float):
        raise ValueError("price must be a Decimal, int or numeric string, not a float or bool")
    try:
        price = value if isinstance(value, Decimal) else Decimal(value)
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError(f"price is not a valid number: {value!r}") from None
    if not price.is_finite():
        raise ValueError("price must be finite")
    if price <= 0:
        raise ValueError("price must be greater than zero")
    if price != price.quantize(_STEP):
        raise ValueError("price has more than 4 decimal places; refusing to round it")
    if price >= _MAX:
        raise ValueError("price is too large for numeric(14,4)")
    return price


def set_price(conn, product_id: int, expected_revision: int | None, new_price, actor: str, origin: str) -> int:
    price = _parse_price(new_price)
    if origin not in _ORIGINS:
        raise ValueError(f"origin must be one of {sorted(_ORIGINS)}, got {origin!r}")
    if not isinstance(actor, str) or not actor.strip():
        raise ValueError("actor must be a non-empty string")

    # conn.transaction() opens the transaction (conn is not autocommit), commits on
    # normal exit and rolls back if anything raises, including StaleRevision.
    with conn.transaction():
        with conn.cursor() as cur:
            # Lock first, then re-check. There may be no row to lock yet (first price),
            # so serialise per product with a transaction-scoped advisory lock;
            # it is released automatically at commit/rollback.
            cur.execute(
                "SELECT pg_advisory_xact_lock(hashtextextended('price_revision:' || %s::text, 0))",
                (product_id,),
            )
            cur.execute(
                "SELECT revision_no FROM price_revision WHERE product_id = %s AND is_current",
                (product_id,),
            )
            row = cur.fetchone()
            current = row[0] if row else None
            if current != expected_revision:
                raise StaleRevision(
                    f"product {product_id}: expected revision {expected_revision}, current is {current}"
                )
            if current is not None:
                cur.execute(
                    "UPDATE price_revision SET is_current = false, superseded_at = now() "
                    "WHERE product_id = %s AND is_current",
                    (product_id,),
                )
            new_revision = (current or 0) + 1
            cur.execute(
                "INSERT INTO price_revision (product_id, revision_no, price, actor, origin) "
                "VALUES (%s, %s, %s, %s, %s)",
                (product_id, new_revision, price, actor, origin),
            )
    logger.info(
        "price set product_id=%s revision=%s actor=%s origin=%s", product_id, new_revision, actor, origin
    )
    return new_revision


def price_history(conn, product_id: int) -> list[tuple[int, Decimal, bool]]:
    # The transaction block ends the implicit transaction, so the connection is not
    # left "idle in transaction" when it goes back to a pool.
    with conn.transaction():
        with conn.cursor() as cur:
            cur.execute(
                "SELECT revision_no, price, is_current FROM price_revision "
                "WHERE product_id = %s ORDER BY revision_no",
                (product_id,),
            )
            return [(r, p, c) for r, p, c in cur.fetchall()]
