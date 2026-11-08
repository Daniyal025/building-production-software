# Internal Q&A Assistant: Plan (~2,000 docs, ~50 users, team-restricted content)

## Ingestion
- **Inventory first.** List every source (PDF folders, wiki spaces), owner, team, last-modified date and sensitivity. Record the access rule for each document at this step, not later.
- **Use connectors, not one-off uploads.** Pull the wiki through its API and PDFs from the file store. Run a nightly incremental sync keyed on content hash, with deletions propagated.
- **Parse by document type.** Use a layout-aware PDF parser that keeps headings and tables. Run OCR only on scanned files. Convert wiki HTML to Markdown and keep the page hierarchy.
- **Chunk along structure.** Split at headings into roughly 300-600 token chunks with small overlap. Prepend the doc title and section path to each chunk. Keep runbook steps and tables intact.
- **Store metadata on every chunk.** Keep doc ID, URL, title, version/date, owner, and the allowed teams/groups. Pull the ACLs from the source system (SSO groups) rather than hand-maintaining them.
- **Flag stale and duplicate content.** Drop exact duplicates and mark superseded versions. Surface the last-updated date in answers.

## Retrieval
- **Use hybrid search.** Combine BM25 with embeddings in one store (Postgres+pgvector, or a managed vector DB that supports metadata filters), then rerank the top ~30 down to ~6 with a cross-encoder. At 2,000 docs there is no need for anything fancier.
- **Enforce permissions at query time, before the LLM sees anything.** Resolve the user's groups from SSO and apply them as a metadata filter inside the search itself. Do not retrieve first and filter afterwards. Never put restricted text in a shared cache or a shared prompt.
- **Keep restricted-doc existence quiet.** If nothing allowed matches, say "I couldn't find this in documents you can access." Do not hint that restricted documents exist.
- **Light query handling.** Rewrite follow-up questions using chat history, and optionally add team or product filters when the question names them.

## Answering
- **Grounded answers with citations.** The prompt says to answer only from the retrieved passages, cite doc title, section and link for every claim, and show the doc's date.
- **Abstain when unsure.** If retrieval scores are low or passages conflict, say so and point to the doc owner or channel. For runbooks and policies, quote the exact text and avoid paraphrasing steps.
- **Safety basics.** Treat document text as untrusted data (prompt injection). Log queries with user ID. Run no tools that act on systems in v1; make it read-only.

## Evaluation
- **Build a golden set of 100-150 questions.** Collect them from real Slack and help-desk questions, with expected source docs and answers. Include permission tests (user A must never get team B's content), unanswerable questions, and conflicting-version cases.
- **Measure retrieval and answers separately.** Retrieval: recall@k and MRR against the expected docs. Answers: faithfulness to sources, correctness and citation accuracy, using an LLM judge calibrated against about 30 human-graded examples.
- **Make permission leakage a hard gate.** Run automated leak tests with a user-per-team matrix on every change. Any leak blocks release.

## Rollout
- **Pilot with 8-10 users across teams for 2-3 weeks.** Add thumbs up/down with a reason, and a "report wrong answer" link to the doc owner. Review all negatives weekly and add them to the golden set.
- **Widen to all 50 in stages.** Deliver it where people already work (Slack or Teams bot, or a simple web UI behind SSO). Publish a short guide on what it covers, what it does not, and how restricted docs behave.
- **Operate it.** Re-run evals on every change to the model, chunking or index. Alert on sync failures, and set a monthly review of unanswered questions to find documentation gaps. Name an owner and keep a per-query cost and latency dashboard (expected to be small at this scale).
