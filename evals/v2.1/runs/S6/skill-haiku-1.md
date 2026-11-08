# Internal Q&A assistant over ~2,000 PDFs and wiki pages

Scope: about 50 employees, some documents restricted to certain teams, read-only answers in the first release.

## Ingestion

- Inventory every source first: owner, format (native PDF, scanned PDF, wiki page), last-modified date, and the teams allowed to read it. Confirm the count against the ~2,000 estimate.
- Extract text per page with page numbers and section headings. Send scanned PDFs through OCR and flag low-confidence pages in the index, rather than indexing empty or garbled text as if it were fine.
- Store on every chunk: source ID, document version, content hash, and the allowed-team list. Re-index only when the hash changes.
- Chunk by heading at roughly 300 to 500 tokens with a small overlap. Repeat the document title and section breadcrumb inside each chunk so it makes sense on its own.
- Sync permissions on a schedule and on every source change. A team removed from a document loses access within a stated window (for example one hour), and deleted or moved documents are removed from the index.

## Retrieval and access control

- Apply the user's team filter inside the search query, before ranking. Never fetch restricted chunks and hide them in the UI afterwards.
- Use hybrid search (keyword plus vector). Policy text is full of exact names, codes and form numbers that pure vector search often misses.
- Route chat, API and any Slack entry point through one retrieval function, so there is only one path that reads documents.
- Keep restricted text out of the model prompt for users who lack access. Include the access scope in any answer cache key, or do not cache answers across users.

## Answering

- Answer only from retrieved passages. Cite the document title, section, page and version for each claim, with a link to the source.
- When retrieval is empty or weak, say "I could not find this in documents you can access" and suggest where to look. Never give a policy figure or rule without a source.
- Treat document text as data. The model must not follow instructions found inside documents, and in this release it cannot change anything.
- Show each source's last-updated date beside the answer, so an old policy is visibly old.

## Evaluation

- Build a golden set of 100 to 150 real questions from employees and document owners, each with the expected source document, before tuning anything. Track retrieval recall at 5 and whether each answer is supported by its citations.
- Add a permission test set: a user from each team must get zero chunks from documents they cannot read. Run it in CI and before each release. Check that it fails against a deliberately leaky version first, so you know it can catch a leak.
- Log questions, retrieved document IDs, no-answer rate and thumbs-down feedback. Keep logs restricted and do not store restricted passage text in them.

## Rollout

- Pilot with 5 to 10 people across two teams for about two weeks, including one team that has restricted documents, before opening it to all 50.
- Name an owner for document quality. Conflicting or stale pages get flagged and fixed at the source, not patched in the assistant.
- Set a per-user rate limit, watch cost and latency, and keep a switch that turns answers off and falls back to plain search.
- Decide on wider rollout or any write actions only after the pilot metrics and the permission tests have passed for a full release cycle.
