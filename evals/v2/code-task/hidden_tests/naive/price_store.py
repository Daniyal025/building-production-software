class StaleRevision(Exception):
    pass


def set_price(conn, product_id, expected_revision, new_price, actor, origin):
    row = conn.execute("SELECT revision_no FROM price_revision WHERE product_id = %s AND is_current", (product_id,)).fetchone()
    current = row[0] if row else None
    if current != expected_revision:
        raise StaleRevision()
    conn.execute("UPDATE price_revision SET is_current = false, superseded_at = now() WHERE product_id = %s AND is_current", (product_id,))
    conn.execute("INSERT INTO price_revision (product_id, revision_no, price, actor, origin) VALUES (%s, %s, %s, %s, %s)",
                 (product_id, (current or 0) + 1, new_price, actor, origin))
    conn.commit()
    return (current or 0) + 1


def price_history(conn, product_id):
    return conn.execute("SELECT revision_no, price, is_current FROM price_revision WHERE product_id = %s ORDER BY revision_no", (product_id,)).fetchall()
