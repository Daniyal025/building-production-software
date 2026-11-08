"""Price writer over the price_revision table (psycopg 3)."""

from decimal import Decimal, InvalidOperation

_ORIGINS = ("ui", "agent_confirmed", "import", "backfill")


class StaleRevision(Exception):
    """The caller's expected revision is not the product's current revision."""


def set_price(conn, product_id: int, expected_revision: int | None, new_price, actor: str, origin: str) -> int:
    """Record a new price for the product and return the new revision number.

    Concurrent callers for the same product are serialized with a transaction-scoped
    advisory lock (it works even when the product has no row yet, which a row lock
    cannot cover). The lock, the stale check, the supersede and the insert all run in
    one transaction that is committed on success and rolled back on any failure.
    """
    # Validate at the boundary so bad input never reaches (or half-writes to) the DB.
    try:
        price = new_price if isinstance(new_price, Decimal) else Decimal(str(new_price))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"invalid price: {new_price!r}") from exc
    if not price.is_finite() or price <= 0:
        raise ValueError(f"price must be a positive finite number: {new_price!r}")
    if origin not in _ORIGINS:
        raise ValueError(f"invalid origin: {origin!r}")
    if not actor:
        raise ValueError("actor is required")

    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT pg_advisory_xact_lock(hashtextextended('price_revision:' || %s::text, 0))",
                (product_id,),
            )
            # Under the lock, the current row (if any) cannot change beneath us.
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
                # Supersede first: the partial unique index allows one current row per product.
                cur.execute(
                    "UPDATE price_revision SET is_current = false, superseded_at = now() "
                    "WHERE product_id = %s AND is_current",
                    (product_id,),
                )
            # Next number from all rows, so numbers are never reused.
            cur.execute(
                "INSERT INTO price_revision (product_id, revision_no, price, actor, origin) "
                "SELECT %s, COALESCE(MAX(revision_no), 0) + 1, %s, %s, %s "
                "FROM price_revision WHERE product_id = %s "
                "RETURNING revision_no",
                (product_id, price, actor, origin, product_id),
            )
            new_revision = cur.fetchone()[0]
        conn.commit()
        return new_revision
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
            rows = cur.fetchall()
        return [(r[0], r[1], r[2]) for r in rows]
    finally:
        conn.rollback()  # end the read-only transaction; don't leave the connection idle-in-transaction
