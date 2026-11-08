"""Price writer over the price_revision table (psycopg 3).

Every set_price is one transaction: serialise per product, check the revision,
supersede the current row, insert the next one, commit. Any failure rolls back.
"""

from decimal import Decimal, InvalidOperation

ORIGINS = {"ui", "agent_confirmed", "import", "backfill"}
MAX_PRICE = Decimal("9999999999.9999")  # numeric(14,4)
_STEP = Decimal("0.0001")


class StaleRevision(Exception):
    """The caller's expected revision is not the product's current revision."""


def _to_price(value) -> Decimal:
    # Floats are refused: 0.1 + 0.2 style values must not become prices silently.
    if isinstance(value, bool) or isinstance(value, float):
        raise TypeError("price must be a Decimal, int or str, not float/bool")
    try:
        price = value if isinstance(value, Decimal) else Decimal(str(value).strip())
    except InvalidOperation:
        raise ValueError(f"invalid price: {value!r}") from None
    if not price.is_finite() or price <= 0:
        raise ValueError(f"price must be a positive finite number: {value!r}")
    # Never round money silently: more than 4 decimals is rejected, not truncated.
    if price != price.quantize(_STEP):
        raise ValueError(f"price has more than 4 decimal places: {value!r}")
    if price > MAX_PRICE:
        raise ValueError(f"price out of range: {value!r}")
    return price


def set_price(conn, product_id: int, expected_revision: int | None, new_price, actor: str, origin: str) -> int:
    """Record a new price and return the new revision number.

    Raises StaleRevision if expected_revision is not the current revision
    (None means "the product has no price yet"). Commits on success; rolls back
    and re-raises on any failure.
    """
    price = _to_price(new_price)
    if origin not in ORIGINS:
        raise ValueError(f"invalid origin: {origin!r}")
    if not actor or not actor.strip():
        raise ValueError("actor is required")

    try:
        with conn.cursor() as cur:
            # Serialises writers of the same product, including the very first
            # price (no row exists yet to lock). Released at commit/rollback.
            # ponytail: shares the advisory-lock keyspace with any other user of it.
            cur.execute("SELECT pg_advisory_xact_lock(%s)", (product_id,))

            cur.execute(
                "SELECT revision_no FROM price_revision"
                " WHERE product_id = %s ORDER BY revision_no DESC LIMIT 1",
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
                    "UPDATE price_revision SET is_current = false, superseded_at = now()"
                    " WHERE product_id = %s AND is_current",
                    (product_id,),
                )
            new_rev = (current or 0) + 1
            cur.execute(
                "INSERT INTO price_revision (product_id, revision_no, price, actor, origin)"
                " VALUES (%s, %s, %s, %s, %s)",
                (product_id, new_rev, price, actor, origin),
            )
        conn.commit()
        return new_rev
    except BaseException:
        conn.rollback()
        raise


def price_history(conn, product_id: int) -> list[tuple[int, Decimal, bool]]:
    """(revision_no, price, is_current) for the product, ordered by revision_no."""
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT revision_no, price, is_current FROM price_revision"
                " WHERE product_id = %s ORDER BY revision_no",
                (product_id,),
            )
            rows = cur.fetchall()
        return [(r[0], r[1], r[2]) for r in rows]
    finally:
        conn.rollback()  # read-only: end the implicit transaction, don't leave it idle
