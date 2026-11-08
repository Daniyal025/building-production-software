# Internal Q&A Assistant Plan (~2,000 docs, ~50 users, restricted docs)

## Ingestion
- **Connectors**: Pull PDFs and wiki pages from their sources (wiki API, file share/Drive) on a nightly schedule, with incremental sync via modified-time or content hash. At this size, a full re-index is cheap, so keep sync simple.
- **ACL capture at ingest**: Store each doc's allowed groups/teams as metadata, copied from the source system (not hand-maintained). Re-sync ACLs on every run, and faster than content (e.g. hourly), so revocations propagate quickly.
- **Parsing**: Use a layout-aware PDF parser. Handle tables, headers/footers and scanned PDFs (OCR only where there is no text layer). Convert wiki pages to clean markdown, keeping heading hierarchy.
- **Chunking**: Split by section/heading (~300-600 tokens, small overlap). Prepend doc title and heading path to each chunk. Keep doc id, URL, page number, last-updated date, owner and ACL as metadata.
- **Dedup and staleness**: Drop duplicate and superseded versions. Store a doc version and date so answers can flag old content.

## Retrieval
- **Hybrid search**: Combine BM25 keyword search (policy names, error codes, acronyms) with embedding search, merged by reciprocal rank fusion. One store such as Postgres+pgvector or a managed vector DB is plenty for ~2k docs.
- **Permission filtering inside the query**: Apply the user's group filter as a pre-filter in the retrieval query. Never retrieve then filter afterwards, and never put restricted text in a shared cache or prompt. This is the most important security rule.
- **Rerank**: Retrieve ~30 candidates, rerank with a cross-encoder or LLM reranker, and pass the top ~6-8 to the model.
- **Query handling**: Rewrite follow-up questions into standalone queries using chat history. Add optional filters (team, doc type) only if evaluation shows they help.

## Answering
- **Grounded generation**: Instruct the model to answer only from the supplied chunks, cite the doc and section for every claim with links, and say "I couldn't find this" when evidence is weak.
- **Freshness and ownership**: Show the doc's last-updated date and owner next to each citation, and flag docs past a review date.
- **Restricted-content behaviour**: If the best answer lies in a doc the user can't access, do not reveal it exists. Say nothing found, or suggest asking the owning team.
- **Safety**: Treat retrieved text as data, not instructions (prompt-injection defence). Don't log full restricted content in shared logs, and keep audit logs of who asked what and which docs were used.

## Evaluation
- **Golden set**: Collect 100-150 real questions from the 50 users and team leads, with expected answer, source doc and the asker's team. Include unanswerable questions and ones spanning multiple docs.
- **Retrieval metrics**: Measure recall@k and MRR against the labelled source docs, and tune chunk size, hybrid weights and reranker on them.
- **Answer metrics**: Score faithfulness (every claim supported by the cited chunk), correctness and appropriate refusal, using an LLM judge calibrated against a human-graded sample of ~30.
- **Access-control tests**: Build adversarial cases: a user from team A asking about team B's restricted doc, direct probing for its title, and prompt injection. The target is zero leaks, and this test runs on every change as a hard gate.

## Rollout
- **Pilot**: Start with 8-10 users across 3-4 teams, including at least one team with restricted docs. Run 2-3 weeks with thumbs up/down and a "report wrong answer" button.
- **Feedback loop**: Review every thumbs-down weekly, add failures to the golden set, and fix the underlying doc, parsing or retrieval. Track unanswered questions to find documentation gaps.
- **Authentication**: Use company SSO, and map groups from the identity provider so the assistant's permissions match the source systems.
- **Full launch**: Expand to all 50 after the pilot meets agreed thresholds (e.g. >85% correct, 0 access leaks). Name an owner, keep a short usage guide, and monitor cost, latency and weekly eval re-runs. Re-run the golden set whenever the model, prompt or index changes.
