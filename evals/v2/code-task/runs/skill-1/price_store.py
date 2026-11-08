"""Append-only price revisions (tier T2: real data, concurrent API callers).

set_price is the single guarded write path: lock the product, re-check the
expected revision, supersede the current row, insert revision + 1, commit.
"""

import logging
from decimal import Decimal, InvalidOperation

import psycopg
from psycopg import errors

log = logging.getLogger(__name__)

ORIGINS = frozenset({"ui", "agent_confirmed", "import", "backfill"})
MAX_PRICE = Decimal("9999999999.9999")  # numeric(14,4)
LOCK_TIMEOUT = "5s"  # every wait is bounded


class StaleRevision(Exception):
    """The caller's expected revision is not the product's current revision."""


def _validate_price(price) -> Decimal:
    # Exact numbers only: floats are refused, never guessed at or rounded.
    if isinstance(price, bool) or isinstance(price, float):
        raise ValueError("price must be a Decimal, int or numeric string, not a float or bool")
    try:
        value = Decimal(price) if not isinstance(price, Decimal) else price
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError(f"price is not a number: {price!r}") from None
    if not value.is_finite():
        raise ValueError("price must be finite")
    if value <= 0:
        raise ValueError("price must be greater than 0")
    if value > MAX_PRICE:
        raise ValueError(f"price must not exceed {MAX_PRICE}")
    if value != value.quantize(Decimal("0.0001")):
        raise ValueError("price has more than 4 decimal places; round it explicitly before saving")
    return value


def set_price(conn, product_id: int, expected_revision: int | None, new_price, actor: str, origin: str) -> int:
    """Record a new price for the product and return the new revision number.

    expected_revision is the revision the caller last saw (None if the product has no price yet);
    raise StaleRevision if it does not match the product's current revision.
    """
    price = _validate_price(new_price)
    if not isinstance(actor, str) or not actor.strip():
        raise ValueError("actor is required")
    if origin not in ORIGINS:
        raise ValueError(f"origin must be one of {sorted(ORIGINS)}")
    if expected_revision is not None and (isinstance(expected_revision, bool) or not isinstance(expected_revision, int)):
        raise ValueError("expected_revision must be an int or None")

    try:
        with conn.cursor() as cur:
            cur.execute(f"SET LOCAL lock_timeout = '{LOCK_TIMEOUT}'")
            # Lock the key itself (works even when the product has no row yet),
            # held until commit/rollback. Check-then-lock would be a race.
            cur.execute("SELECT pg_advisory_xact_lock(%s)", (product_id,))
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
        conn.commit()
        return new_revision
    except errors.UniqueViolation as exc:
        # A writer that bypassed this function got in between; treat as a lost race.
        conn.rollback()
        raise StaleRevision(f"product {product_id}: concurrent write detected") from exc
    except BaseException:
        conn.rollback()
        raise


def price_history(conn, product_id: int) -> list[tuple[int, Decimal, bool]]:
    """(revision_no, price, is_current) for the product, ordered by revision_no."""
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT revision_no, price, is_current FROM price_revision "
                "WHERE product_id = %s ORDER BY revision_no",
                (product_id,),
            )
            return [(r[0], r[1], r[2]) for r in cur.fetchall()]
    finally:
        conn.rollback()  # don't leave the connection idle in a transaction
