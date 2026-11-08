from decimal import Decimal


class StaleRevision(Exception):
    pass


def set_price(conn, product_id: int, expected_revision: int | None, new_price, actor: str, origin: str) -> int:
    """Supersede the product's current price with new_price; return the new revision number."""
    price = new_price if isinstance(new_price, Decimal) else Decimal(str(new_price))
    try:
        with conn.cursor() as cur:
            # Serialise writers per product, including the "no current row yet" case
            # that row locks cannot cover. Released at commit/rollback.
            cur.execute(
                "SELECT pg_advisory_xact_lock(hashtextextended('price_revision:' || %s::text, 0))",
                (product_id,),
            )
            cur.execute(
                "SELECT revision_no FROM price_revision WHERE product_id = %s AND is_current FOR UPDATE",
                (product_id,),
            )
            row = cur.fetchone()
            current = row[0] if row else None
            if current != expected_revision:
                raise StaleRevision(
                    f"product {product_id}: expected revision {expected_revision}, current is {current}"
                )
            if current is not None:
                # Must precede the insert: the partial unique index allows one current row.
                cur.execute(
                    "UPDATE price_revision SET is_current = false, superseded_at = now() "
                    "WHERE product_id = %s AND is_current",
                    (product_id,),
                )
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
            return [(r[0], r[1], r[2]) for r in cur.fetchall()]
    finally:
        conn.rollback()  # read-only; don't leave the connection idle in transaction
