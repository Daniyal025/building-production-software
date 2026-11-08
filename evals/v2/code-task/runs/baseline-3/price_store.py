from decimal import Decimal

from psycopg import errors


class StaleRevision(Exception):
    pass


def set_price(conn, product_id: int, expected_revision: int | None, new_price, actor: str, origin: str) -> int:
    price = new_price if isinstance(new_price, Decimal) else Decimal(str(new_price))
    try:
        with conn.cursor() as cur:
            # The UPDATE takes the row lock on the current revision, so concurrent writers
            # for the same product serialize here; a waiter re-checks is_current after the
            # winner commits and then sees no current row.
            cur.execute(
                "UPDATE price_revision SET is_current = false, superseded_at = now() "
                "WHERE product_id = %s AND is_current RETURNING revision_no",
                (product_id,),
            )
            row = cur.fetchone()
            current = row[0] if row else None
            if current != expected_revision:
                raise StaleRevision(
                    f"product {product_id}: expected revision {expected_revision}, current is {current}"
                )
            cur.execute(
                "SELECT COALESCE(MAX(revision_no), 0) + 1 FROM price_revision WHERE product_id = %s",
                (product_id,),
            )
            next_no = cur.fetchone()[0]
            cur.execute(
                "INSERT INTO price_revision (product_id, revision_no, price, actor, origin) "
                "VALUES (%s, %s, %s, %s, %s)",
                (product_id, next_no, price, actor, origin),
            )
        conn.commit()
        return next_no
    except errors.UniqueViolation as e:
        # Two first-time writers (no row to lock) racing on the same revision.
        conn.rollback()
        raise StaleRevision(f"product {product_id}: concurrent price change") from e
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
        conn.rollback()  # end the read-only transaction so the connection isn't left idle-in-transaction
    return rows
