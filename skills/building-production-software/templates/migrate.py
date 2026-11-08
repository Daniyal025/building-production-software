#!/usr/bin/env python3
"""Forward-only Postgres migration runner with a checksummed ledger.

Usage:
    DATABASE_URL=postgresql://user@host/db python migrate.py [--dir migrations] [--dry-run]

- Applies files named like 0001_create_users.sql in name order, each in its own transaction.
- Records version, sha256, applied_at and applied_by in schema_migrations.
- Refuses to run if an applied file changed or disappeared: fix forward with a new file.
- Takes an advisory lock first, so two runners can never interleave.
- Files must not contain BEGIN/COMMIT, or statements that can't run in a transaction
  (e.g. CREATE INDEX CONCURRENTLY); put those in a separate, documented step.

Requires: psycopg >= 3 (pip install "psycopg[binary]").
"""
import argparse
import hashlib
import os
import pathlib
import sys

import psycopg

LEDGER = """
CREATE TABLE IF NOT EXISTS schema_migrations (
    version    text PRIMARY KEY,
    sha256     text NOT NULL,
    applied_at timestamptz NOT NULL DEFAULT now(),
    applied_by text NOT NULL DEFAULT current_user
)"""


def plan(applied: dict[str, str], files: list[pathlib.Path]):
    """Return (files to apply, refusal reasons). Pure, so it is easy to test."""
    todo, errors = [], []
    for f in files:
        digest = hashlib.sha256(f.read_bytes()).hexdigest()
        if f.stem not in applied:
            todo.append((f, digest))
        elif applied[f.stem] != digest:
            errors.append(f"{f.name}: changed after it was applied (fix forward with a new file)")
    present = {f.stem for f in files}
    errors += [f"{v}: recorded as applied but the file is missing" for v in sorted(set(applied) - present)]
    return todo, errors


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dir", default="migrations")
    ap.add_argument("--dry-run", action="store_true", help="list what would run, change nothing")
    args = ap.parse_args(argv)
    files = sorted(pathlib.Path(args.dir).glob("[0-9]*.sql"))

    with psycopg.connect(os.environ["DATABASE_URL"], autocommit=True) as conn:
        conn.execute("SELECT pg_advisory_lock(hashtext('schema_migrations'))")
        conn.execute(LEDGER)
        applied = dict(conn.execute("SELECT version, sha256 FROM schema_migrations").fetchall())
        todo, errors = plan(applied, files)
        if errors:
            for e in errors:
                print("REFUSED " + e, file=sys.stderr)
            return 2
        for f, digest in todo:
            print(("would apply " if args.dry_run else "applying ") + f.name)
            if args.dry_run:
                continue
            with conn.transaction():
                conn.execute(f.read_text(encoding="utf-8"))
                conn.execute(
                    "INSERT INTO schema_migrations (version, sha256) VALUES (%s, %s)", (f.stem, digest)
                )
        print("up to date" if not todo else f"{len(todo)} migration(s) {'pending' if args.dry_run else 'applied'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
