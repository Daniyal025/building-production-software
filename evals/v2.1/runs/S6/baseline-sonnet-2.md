# Internal Q&A assistant over ~2,000 PDFs and wiki pages (50 users, team-restricted docs)

## Ingestion
- **Connectors first.** Pull wiki pages through the wiki's API and PDFs from their source (drive or repo). Run a nightly incremental sync keyed on a content hash, and delete vectors for documents that were removed. At ~2,000 docs, a full re-index costs pennies, so keep this simple.
- **Parse for structure.** Convert to text or markdown that keeps headings, tables and lists. Use a layout-aware parser for PDFs, and OCR only the scanned ones. Flag docs that parse badly (empty or garbled) and review them by hand instead of ingesting junk.
- **Chunk by section.** Use heading-aware chunks of about 300–600 tokens with a small overlap. Prefix each chunk with its doc title and heading path, and keep tables whole.
- **Metadata on every chunk.** Store doc ID, title, URL, owner, last-modified date, doc type, and the ACL (allowed groups). Take the ACL from the source system (wiki space permissions, drive sharing) and not from a hand-kept list. Docs with no resolvable ACL default to deny.
- **Handle staleness and duplicates.** Record version and date. Collapse near-duplicates and prefer the newest. Surface "last updated" in answers so people can judge currency.

## Retrieval
- **Hybrid search.** Combine BM25 and dense embeddings, merge with reciprocal rank fusion, then rerank the top ~30 down to ~6–8 with a cross-encoder or hosted reranker. Policies and runbooks are full of exact terms (error codes, system names) that pure vector search misses.
- **Enforce access control in the query, not after generation.** Resolve the user's groups from SSO at request time and apply them as a metadata filter inside the vector and keyword search. Restricted chunks never reach the prompt, so they cannot leak through the answer, citations or "I couldn't find..." messages.
- **Use one store.** Postgres with pgvector and full-text search is enough at this scale. It keeps the ACL filter, sync and backups in one place. Don't add a dedicated vector DB.
- **Light query handling.** Rewrite follow-up questions into standalone queries using chat history. Skip fancier tricks (HyDE, multi-hop agents) until the eval set shows a gap.

## Answering
- **Grounded answers with citations.** The prompt allows only the retrieved context. Every claim cites doc title, section and link, and the cited chunk must be in the context.
- **Abstain well.** If retrieval confidence is low or the sources conflict, say so and point to the likely owner or team. Don't guess. For policy questions, show the source's date and quote the key line.
- **Treat docs as untrusted input.** Tell the model that retrieved text is data and not instructions, which guards against prompt injection from wiki content. The assistant is read-only and has no tools that act on anything.
- **Pick the model by cost and quality.** One strong mid-tier model is plenty at 50 users. Stream responses, and log the query, retrieved chunk IDs and answer to a store with the same access controls.

## Evaluation
- **Build a gold set of 100–150 questions** from real employee questions (Slack, helpdesk), with expected source docs and short reference answers. Include about 15% unanswerable questions and a slice of restricted-doc questions.
- **Measure retrieval and answers separately.** For retrieval, track recall@k and MRR against the expected docs. For answers, track faithfulness (is every claim supported by the cited chunks), correctness and citation accuracy. Use an LLM judge calibrated against about 30 hand-graded examples.
- **Test access control explicitly.** Build a permission suite: for each restricted doc, a user outside the group asks a question only that doc answers. The expected result is no content, no title, and no citation. Run it in CI on every change to ingestion or retrieval, and treat any failure as release-blocking.
- **Regression gating.** Re-run the full eval on every change to chunking, embeddings, reranker, prompt or model, and compare to the last run before shipping.

## Rollout
- **Phase it.** Start with a 5–8 person pilot across 2–3 teams, including at least one with restricted docs. Move to a 50-user launch once the gold-set and permission thresholds hold and pilot feedback is acceptable.
- **Close the feedback loop.** Add thumbs up/down with a reason, a "wrong or outdated doc" report that routes to the doc owner, and a weekly review of low-rated and abstained queries. Fix content gaps in the docs themselves, not only in the retrieval.
- **Operate it.** Put it behind SSO in Slack or a small web app. Add an audit log of who asked what and which restricted docs were retrieved, alerts on sync failures, a cost budget, and a named owner. Re-run the eval monthly and when the doc set changes materially.
