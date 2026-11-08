"""Append-only price revisions (tier T2: real data, concurrent web API).

set_price is the single guarded write path: validate -> lock the product ->
re-check the expected revision -> supersede the old row -> insert revision + 1,
all in one transaction. Callers map StaleRevision to HTTP 409.
"""

import logging
from decimal import Decimal, InvalidOperation

logger = logging.getLogger(__name__)

ORIGINS = {"ui", "agent_confirmed", "import", "backfill"}  # mirrors the schema CHECK
_MAX = Decimal(10) ** 10  # numeric(14,4): at most 10 integer digits
_STEP = Decimal("0.0001")
_LOCK_TIMEOUT = "5s"  # a stuck writer must not hang every other request


class StaleRevision(Exception):
    """expected_revision does not match the product's current revision."""


def _validate_price(value) -> Decimal:
    """Exact Decimal or ValueError. Floats are refused (binary error), and so is
    anything numeric(14,4) would round or overflow: the DB must never store a
    different number than the caller sent."""
    if isinstance(value, bool) or isinstance(value, float):
        raise ValueError("price must be a Decimal, int or numeric string, not a float or bool")
    try:
        price = Decimal(value)
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError(f"price is not a number: {value!r}") from None
    if not price.is_finite() or price <= 0 or price >= _MAX:
        raise ValueError(f"price must be finite, > 0 and < {_MAX}: {value!r}")
    if price != price.quantize(_STEP):
        raise ValueError(f"price has more than 4 decimal places (would be rounded): {value!r}")
    return price


def set_price(conn, product_id: int, expected_revision: int | None, new_price, actor: str, origin: str) -> int:
    price = _validate_price(new_price)
    if not isinstance(actor, str) or not actor.strip():
        raise ValueError("actor is required")
    if origin not in ORIGINS:
        raise ValueError(f"origin must be one of {sorted(ORIGINS)}: {origin!r}")

    try:
        with conn.cursor() as cur:
            cur.execute(f"SET LOCAL lock_timeout = '{_LOCK_TIMEOUT}'")
            # Serialise writers per product. A row lock can't do it: the first
            # price has no row yet. Transaction-scoped, so commit/rollback frees it.
            # ponytail: shares the global advisory-lock keyspace; use the
            # (classid, objid) form if other code adds advisory locks.
            cur.execute("SELECT pg_advisory_xact_lock(%s)", (product_id,))
            cur.execute(
                "SELECT id, revision_no FROM price_revision WHERE product_id = %s AND is_current",
                (product_id,),
            )
            row = cur.fetchone()
            current = row[1] if row else None
            if current != expected_revision:
                raise StaleRevision(
                    f"product {product_id}: expected revision {expected_revision}, current is {current}"
                )
            if row:
                cur.execute(
                    "UPDATE price_revision SET is_current = false, superseded_at = now() WHERE id = %s",
                    (row[0],),
                )
            new_rev = (current or 0) + 1
            cur.execute(
                "INSERT INTO price_revision (product_id, revision_no, price, actor, origin) "
                "VALUES (%s, %s, %s, %s, %s)",
                (product_id, new_rev, price, actor, origin),
            )
        conn.commit()
    except BaseException:
        conn.rollback()  # leave the DB unchanged and the connection reusable
        raise
    logger.info("price set product=%s revision=%s actor=%s origin=%s", product_id, new_rev, actor, origin)
    return new_rev


def price_history(conn, product_id: int) -> list[tuple[int, Decimal, bool]]:
    # conn.transaction() ends the read's implicit transaction (no idle-in-transaction
    # connection left in the pool) without committing anything of the caller's.
    with conn.transaction(), conn.cursor() as cur:
        cur.execute(
            "SELECT revision_no, price, is_current FROM price_revision "
            "WHERE product_id = %s ORDER BY revision_no",
            (product_id,),
        )
        return [tuple(r) for r in cur.fetchall()]


if __name__ == "__main__":  # no-DB self-check of the validation rules
    assert _validate_price("12.5") == Decimal("12.5") and _validate_price(3) == 3
    for bad in (1.5, True, "abc", None, 0, -1, "NaN", "Infinity", "1.00001", 10**10):
        try:
            _validate_price(bad)
        except ValueError:
            continue
        raise AssertionError(f"accepted {bad!r}")
    print("ok")
