# Internal Q&A Assistant: Plan

Scope: ~2,000 internal PDFs and wiki pages (policies, runbooks, product docs), ~50 employees, some documents restricted to specific teams.

## Ingestion

- Inventory every source (PDF, wiki export, shared drive) into one manifest: source ID, owner, last-modified date, and the team ACL it inherits.
- Extract text per page; run OCR only on scanned PDFs, flagged by low text density. Keep page numbers for citations.
- Normalise to one document record: title, source URL, section headings, ACL, version, and content hash.
- Chunk by heading section (roughly 300 to 800 tokens) with a small overlap, and keep the heading path as metadata.
- Deduplicate on content hash and near-duplicate similarity so superseded copies do not compete in retrieval.
- Re-ingest incrementally on change (webhook or nightly diff), and drop chunks whose source was deleted.

## Access control

- Store each chunk's allowed teams as metadata, copied from the source ACL at ingest time.
- Apply the filter inside the retrieval query (pre-filter), never after the model has seen the text.
- Resolve the asker's team memberships from the identity provider at query time, not from a cached copy.
- Log every query and the chunk IDs returned, so access can be audited later.

## Retrieval

- Use hybrid search: keyword (BM25) plus vector similarity, merged with reciprocal rank fusion. Keyword matters for policy codes and product names.
- Rerank the top 30 to 50 candidates and pass about 5 to 8 chunks to the model.
- Return the source title, section, and page with every chunk so answers can cite them.

## Answering

- Answer only from retrieved chunks. If nothing relevant is found, say so rather than guessing.
- Require an inline citation for each claim, and show the linked source beneath the answer.
- Show the document's last-updated date, and warn when the best match is older than its policy's review window.

## Evaluation

- Build a gold set of 100 to 150 real questions with expected source documents, written with the team leads who own each area.
- Include restricted-document questions, asked as users with and without access, to test that the ACL holds (target: zero leaks).
- Measure retrieval recall at 5 and answer faithfulness (every claim supported by a cited chunk), and track refusals on out-of-scope questions.

## Rollout

- Pilot with 5 to 10 users from two teams for two weeks, collecting thumbs up/down and "wrong source" reports.
- Fix the gold set and chunking based on pilot failures, then open to all 50 employees.
- Set an owner for each document area to correct or retire stale content, since the assistant is only as current as its sources.
