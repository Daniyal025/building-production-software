"""Price writer: append-only revisions, one current row per product."""

from decimal import Decimal, InvalidOperation

import psycopg
from psycopg import errors

ORIGINS = {"ui", "agent_confirmed", "import", "backfill"}
_MAX = Decimal(10) ** 10  # numeric(14,4): at most 10 integer digits


class StaleRevision(Exception):
    """The caller's expected revision is not the product's current one."""


def _validate_price(price) -> Decimal:
    # Floats are rejected: a binary float is not the exact number the caller meant.
    if isinstance(price, bool) or isinstance(price, float):
        raise TypeError("price must be a Decimal, int or str, not float/bool")
    try:
        d = Decimal(price)
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError(f"invalid price: {price!r}") from None
    if not d.is_finite() or d <= 0 or d >= _MAX:
        raise ValueError(f"price out of range: {price!r}")
    if d != d.quantize(Decimal("0.0001")):  # never let the column round silently
        raise ValueError(f"price has more than 4 decimal places: {price!r}")
    return d


def set_price(conn, product_id: int, expected_revision: int | None, new_price, actor: str, origin: str) -> int:
    price = _validate_price(new_price)
    if origin not in ORIGINS:
        raise ValueError(f"invalid origin: {origin!r}")
    if not actor or not actor.strip():
        raise ValueError("actor is required")

    try:
        with conn.cursor() as cur:
            # Lock the current row so concurrent writers for this product serialize.
            cur.execute(
                "SELECT id, revision_no FROM price_revision "
                "WHERE product_id = %s AND is_current FOR UPDATE",
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
            # max(), not current+1: revision numbers stay unique even if history has gaps.
            cur.execute(
                "SELECT COALESCE(MAX(revision_no), 0) + 1 FROM price_revision WHERE product_id = %s",
                (product_id,),
            )
            new_rev = cur.fetchone()[0]
            cur.execute(
                "INSERT INTO price_revision (product_id, revision_no, price, actor, origin) "
                "VALUES (%s, %s, %s, %s, %s)",
                (product_id, new_rev, price, actor, origin),
            )
        conn.commit()
        return new_rev
    except errors.UniqueViolation:
        # Two first-ever writers (no row to lock) raced; the loser saw a stale state.
        conn.rollback()
        raise StaleRevision(f"product {product_id}: concurrent write won") from None
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
        return [(r[0], r[1], r[2]) for r in rows]
    finally:
        conn.rollback()  # read-only: don't leave the connection idle in a transaction
