-- Append-only history with exactly one current row per key, plus one guarded writer.
-- Pattern: every write goes through supersede_price(); nothing UPDATEs prices directly.
-- Rename "price"/"product" to your entity. Postgres 12+.

CREATE TABLE price_revision (
    id            bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    product_id    bigint        NOT NULL,            -- REFERENCES product (id) in your schema
    revision_no   integer       NOT NULL CHECK (revision_no > 0),
    price         numeric(14,4) NOT NULL CHECK (price > 0),
    is_current    boolean       NOT NULL DEFAULT true,
    valid_from    timestamptz   NOT NULL DEFAULT now(),
    superseded_at timestamptz,
    actor         text          NOT NULL,            -- who: user id, service name
    origin        text          NOT NULL CHECK (origin IN ('ui', 'agent_confirmed', 'import', 'backfill')),
    UNIQUE (product_id, revision_no),
    CHECK (is_current = (superseded_at IS NULL))
);

-- At most one current row per product, enforced by the database, not by convention.
CREATE UNIQUE INDEX price_revision_one_current ON price_revision (product_id) WHERE is_current;

-- The one guarded writer: lock, re-check the caller's expected revision, supersede, insert.
-- p_expected is the revision the caller last saw (NULL for a product with no price yet).
-- A mismatch raises SQLSTATE 'SR409' -> map it to HTTP 409 "someone else changed this; reload".
CREATE FUNCTION supersede_price(
    p_product bigint, p_expected integer, p_price numeric, p_actor text, p_origin text
) RETURNS integer
LANGUAGE plpgsql AS $$
DECLARE
    cur integer;
BEGIN
    -- Serialise writers for this product, including the very first insert.
    PERFORM pg_advisory_xact_lock(hashtextextended('price_revision:' || p_product, 0));

    SELECT revision_no INTO cur
      FROM price_revision
     WHERE product_id = p_product AND is_current;

    IF cur IS DISTINCT FROM p_expected THEN
        RAISE EXCEPTION 'stale revision for product %: expected %, current %', p_product, p_expected, cur
              USING ERRCODE = 'SR409';
    END IF;

    UPDATE price_revision
       SET is_current = false, superseded_at = now()
     WHERE product_id = p_product AND is_current;

    INSERT INTO price_revision (product_id, revision_no, price, actor, origin)
    VALUES (p_product, coalesce(cur, 0) + 1, p_price, p_actor, p_origin);

    RETURN coalesce(cur, 0) + 1;
END
$$;
