# Code task: a price writer

Write a Python module `price_store.py` (psycopg 3, Python 3.12) against the schema in `schema.sql`, which has already been applied. It must expose:

```python
class StaleRevision(Exception): ...

def set_price(conn, product_id: int, expected_revision: int | None, new_price, actor: str, origin: str) -> int:
    """Record a new price for the product and return the new revision number.
    expected_revision is the revision the caller last saw (None if the product has no price yet);
    raise StaleRevision if it does not match the product's current revision."""

def price_history(conn, product_id: int) -> list[tuple[int, Decimal, bool]]:
    """(revision_no, price, is_current) for the product, ordered by revision_no."""
```

- `conn` is an open `psycopg.Connection` (not in autocommit mode).
- Each `set_price` call is its own unit of work: it commits on success and leaves the database unchanged on failure.
- The module will be called from a web API that serves concurrent requests. Write it at production quality.
- No database is available to you while writing. Write the file only.
