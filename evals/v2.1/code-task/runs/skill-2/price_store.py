"""Append-only price history with optimistic concurrency (psycopg 3)."""

from decimal import Decimal, InvalidOperation

import psycopg
from psycopg import errors

ORIGINS = {"ui", "agent_confirmed", "import", "backfill"}
MAX_PRICE = Decimal("9999999999.9999")  # numeric(14,4)


class StaleRevision(Exception):
    """The caller's expected revision is not the product's current revision."""


def _validate_price(value) -> Decimal:
    # Floats are rejected: an inexact binary value must never become a price.
    if isinstance(value, bool) or isinstance(value, float):
        raise ValueError("price must be a Decimal, int or str, not float/bool")
    try:
        price = Decimal(value)
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError(f"invalid price: {value!r}") from None
    if not price.is_finite() or price <= 0 or price > MAX_PRICE:
        raise ValueError(f"price out of range: {value!r}")
    # The column holds 4 decimals; refuse to round silently.
    if price != price.quantize(Decimal("0.0001")):
        raise ValueError(f"price has more than 4 decimal places: {value!r}")
    return price


def set_price(conn, product_id: int, expected_revision: int | None, new_price, actor: str, origin: str) -> int:
    price = _validate_price(new_price)
    if origin not in ORIGINS:
        raise ValueError(f"invalid origin: {origin!r}")
    if not actor or not actor.strip():
        raise ValueError("actor is required")

    try:
        with conn.cursor() as cur:
            # Serialise writers per product. There is no product row to lock, and
            # FOR UPDATE on a not-yet-existing first revision would not block anyone.
            # Released automatically at commit/rollback.
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
                # Supersede first: the partial unique index allows one current row.
                cur.execute(
                    "UPDATE price_revision SET is_current = false, superseded_at = now() "
                    "WHERE product_id = %s AND is_current",
                    (product_id,),
                )
            new_rev = (current or 0) + 1
            cur.execute(
                "INSERT INTO price_revision (product_id, revision_no, price, actor, origin) "
                "VALUES (%s, %s, %s, %s, %s)",
                (product_id, new_rev, price, actor, origin),
            )
        conn.commit()
        return new_rev
    except errors.UniqueViolation:
        # A writer that bypassed the lock got there first: same meaning as stale.
        conn.rollback()
        raise StaleRevision(f"product {product_id}: concurrent write") from None
    except BaseException:
        conn.rollback()
        raise


def price_history(conn, product_id: int) -> list[tuple[int, Decimal, bool]]:
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT revision_no, price, is_current FROM price_revision "
                "WHERE product_id = %s ORDER BY revision_no",
                (product_id,),
            )
            rows = cur.fetchall()
    finally:
        conn.rollback()  # end the read-only transaction; do not leave the connection idle-in-transaction
    return [(r[0], r[1], r[2]) for r in rows]
