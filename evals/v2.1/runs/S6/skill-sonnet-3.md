# Internal Q&A assistant: plan (about 2,000 docs, 50 users, team-restricted content)

The main risk is not answer quality. It is an employee seeing, through an answer, a document they are not allowed to open. The plan is built around that.

## Ingestion

- **Connectors and inventory:** Pull from the wiki API and the PDF store (or a shared drive) on a schedule, not by manual upload. Keep a document table with source ID, URL, owner, content hash, last-modified date and ACL. At this size a nightly full sync plus webhook or hourly deltas is enough.
- **Copy the access rules at ingest:** Record each document's allowed groups from the source system (wiki space permissions, folder ACLs) and store them on every chunk. Map to your identity provider's groups, not to individual users. A document with no resolvable ACL is not indexed. It is quarantined and listed for a human to fix.
- **Parse by document type, and fail loudly:** Use a layout-aware parser for PDFs (tables, headings) and OCR only for scans. A file that parses to zero text, or fails to parse, fails that document's sync and names the file in a report. It must never be silently skipped, because "the assistant doesn't know X" would then look like "X doesn't exist".
- **Chunk by structure:** Split on headings and keep the heading path, document title, team and date with every chunk (roughly 300-800 tokens, small overlap). Runbook steps and policy clauses should not be cut mid-list. Keep the raw files and parsed text, deduplicated by hash, so a parser or chunking fix can be replayed without re-fetching.
- **Deletes and revisions:** When a source doc is deleted, moved or its permissions are tightened, remove or re-tag its chunks in the next sync. Run an overdue-sync alert that is independent of the sync job itself. Stale permissions are the worst failure here.

## Retrieval

- **Filter by permission inside the query:** Resolve the user's groups from the login, then apply the ACL filter in the vector or keyword query itself, before ranking. Never retrieve first and filter afterwards, and never rely on the prompt to "not mention" restricted content. The model only ever sees chunks the user may read.
- **Hybrid search plus rerank:** Combine keyword search (BM25, important for policy numbers, system names and error strings) with embeddings, then rerank the top 30-50 down to 5-8. Postgres with pgvector and full-text search is enough for this corpus. No dedicated vector database is needed.
- **Prefer current documents:** Boost newer and "approved" docs, and demote or flag anything marked superseded or older than a set age. Conflicting versions of a policy are the most common cause of wrong answers in this kind of corpus.

## Answering

- **Grounded, cited answers only:** The model answers from the retrieved chunks and cites document title, section, link and last-updated date for each claim. Check on the server that every citation points to a chunk that was actually retrieved for this user. If the evidence is weak or absent, say "I couldn't find this" and suggest the likely owning team. Do not guess.
- **Restricted-content behaviour:** If the best match is one the user can't access, the assistant must not reveal that it exists or confirm anything about it. It gives the same "not found" answer as for a missing document. Optionally offer a generic "ask the document owner" path that doesn't name the document.
- **Treat documents as untrusted input:** Wiki pages can contain text like "ignore previous instructions". Keep instructions in the system prompt, mark retrieved text as data, give the model no tools that write or send anything, and add injection test cases (see evaluation).
- **Log what's needed, not everything:** Per query, record user, retrieved chunk IDs, model and version, token counts, latency and the user's thumbs up/down. Do not store full prompt and answer text by default, because the logs would become a second, unprotected copy of restricted content. Add per-user rate and cost limits.

## Evaluation

- **Build a labelled question set before launch:** Collect 100-150 real questions from Slack, the helpdesk and onboarding, each with the correct source document and expected answer. Include questions that should return "not found", ambiguous ones, and ones where old and new versions conflict. Have team leads label them, not engineers.
- **Measure retrieval separately from answers:** Track recall@k (was the right chunk retrieved?) apart from answer correctness and citation accuracy. Most "bad answers" turn out to be retrieval or parsing problems, and mixing the two metrics hides which one it is.
- **Permission tests are release blockers:** Make a set of test users (one per team, plus one with no teams) and queries aimed at restricted docs, including paraphrases, "summarise the HR doc" prompts and injection attempts. The pass bar is zero restricted chunks retrieved and zero leaked facts. Run it on every change to ingestion, retrieval, the prompt or the model, and also after each ACL sync.
- **Gate changes on the set:** Version the prompt, embedding model and LLM. A change ships only if the eval set meets its agreed thresholds (set them from the first baseline run), and keep a one-step rollback to the previous version. Add every bad answer reported in production to the set as a new case.

## Rollout

- **Pilot with 8-10 people across at least three teams:** Include at least one person from each restricted team. Run it for 2-3 weeks with a visible feedback button on every answer, and review all thumbs-down and "not found" results weekly. Fix the sources (outdated pages, missing docs) as well as the system.
- **Widen in stages, with owners:** Go to all 50 once the permission tests pass and answer quality meets the agreed bar on the real-question set. Name one owner for the corpus (sync health, stale pages) and one for the assistant (evals, prompts, cost). Document who adds new sources and how their access rules are mapped.
- **Rollback and ongoing checks:** Keep a switch to turn off the restricted sources only (or the whole assistant) without a deploy. Re-run the eval set weekly against live data to catch drift, and review the access-group mapping with IT each quarter and whenever someone changes team.
