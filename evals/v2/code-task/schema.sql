CREATE TABLE price_revision (
    id            bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    product_id    bigint        NOT NULL,
    revision_no   integer       NOT NULL CHECK (revision_no > 0),
    price         numeric(14,4) NOT NULL CHECK (price > 0),
    is_current    boolean       NOT NULL DEFAULT true,
    valid_from    timestamptz   NOT NULL DEFAULT now(),
    superseded_at timestamptz,
    actor         text          NOT NULL,
    origin        text          NOT NULL CHECK (origin IN ('ui', 'agent_confirmed', 'import', 'backfill')),
    UNIQUE (product_id, revision_no),
    CHECK (is_current = (superseded_at IS NULL))
);
CREATE UNIQUE INDEX price_revision_one_current ON price_revision (product_id) WHERE is_current;
