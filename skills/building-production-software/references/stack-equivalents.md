# Stack equivalents

The rules are stack-neutral; the examples use Python, Postgres and React. Map them to your stack:

| Example in this skill | Equivalents |
|---|---|
| `Decimal` + `NUMERIC` | Java `BigDecimal`; .NET `decimal`; Go `shopspring/decimal`; JS/TS strings + `decimal.js`/`big.js`; MySQL `DECIMAL`; MongoDB `Decimal128` |
| `pg_advisory_xact_lock` | MySQL `GET_LOCK`; SQL Server `sp_getapplock`; `SELECT … FOR UPDATE` on a lock row; Redis lock with a fencing token |
| Partial unique index `WHERE is_current` | SQL Server filtered index; MySQL unique index on a generated column that is NULL when not current; MongoDB partial index |
| `NOT VALID` then `VALIDATE` | Add the constraint after a backfill; online schema tools (gh-ost, pt-online-schema-change) |
| Migration ledger tool | Flyway, Liquibase, Alembic, Django/Rails migrations, golang-migrate, Prisma Migrate — all keep a ledger; never edit applied files |
| Pydantic request models | zod / valibot (TS), Bean Validation (Java), FluentValidation (.NET), go-playground/validator |
| FastAPI router-level auth dependency | Express/Fastify router middleware, Spring Security filter chain, ASP.NET fallback `[Authorize]` policy, NestJS global guard |
| OpenAPI codegen / zod at the boundary | openapi-typescript, orval, tRPC, GraphQL codegen, gRPC/protobuf |
| TanStack Query mutation hook | SWR `mutate`, RTK Query, Apollo mutations — one shared hook either way |
| pytest + clock injection | freezegun / time-machine; Jest/Vitest fake timers; Java `Clock`; a Go clock interface |
| `uv sync --frozen` | `npm ci`, `pnpm install --frozen-lockfile`, `poetry install --sync`, `go mod download` + `go.sum`, `cargo build --locked` |
| Docker Compose file secrets | Kubernetes Secrets mounted as files, AWS/GCP/Azure secret managers, HashiCorp Vault |
