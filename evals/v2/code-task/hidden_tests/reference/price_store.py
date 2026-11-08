from decimal import Decimal

import psycopg


class StaleRevision(Exception):
    pass


def set_price(conn, product_id, expected_revision, new_price, actor, origin):
    if not isinstance(new_price, Decimal) or not new_price.is_finite():
        raise TypeError("new_price must be a finite Decimal")
    try:
        with conn.transaction():
            conn.execute("SELECT pg_advisory_xact_lock(hashtextextended('price:' || %s::text, 0))", (product_id,))
            row = conn.execute(
                "SELECT revision_no FROM price_revision WHERE product_id = %s AND is_current", (product_id,)
            ).fetchone()
            current = row[0] if row else None
            if current != expected_revision:
                raise StaleRevision(f"expected {expected_revision}, current {current}")
            conn.execute(
                "UPDATE price_revision SET is_current = false, superseded_at = now() WHERE product_id = %s AND is_current",
                (product_id,),
            )
            new_rev = (current or 0) + 1
            conn.execute(
                "INSERT INTO price_revision (product_id, revision_no, price, actor, origin) VALUES (%s, %s, %s, %s, %s)",
                (product_id, new_rev, new_price, actor, origin),
            )
        conn.commit()
        return new_rev
    except BaseException:
        conn.rollback()
        raise


def price_history(conn, product_id):
    rows = conn.execute(
        "SELECT revision_no, price, is_current FROM price_revision WHERE product_id = %s ORDER BY revision_no",
        (product_id,),
    ).fetchall()
    conn.commit()
    return rows
