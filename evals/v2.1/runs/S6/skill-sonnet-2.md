# Internal Q&A assistant: plan

2,000 documents and 50 users is small. A single Postgres with pgvector plus full-text search is enough. Restricted documents are the one place where I would not cut corners.

## Ingestion

- **Sources and ownership.** Connect the wiki and the PDF store directly (API or sync), not by manual upload. Every document gets an owner, a source URL, a last-modified date and an access list taken from the source system.
- **Permissions travel with the data.** Store the allowed teams or groups on every chunk. Re-sync permissions on a short schedule, and sooner on a webhook, so that revoking access takes effect within minutes. Unknown or missing permissions mean the chunk is treated as restricted, never as open.
- **Parsing fails loudly.** A PDF that parses to zero text (scanned, encrypted, broken tables) fails the run and is named in a report. Do not silently skip it. Add OCR only for the documents that need it.
- **Structure-aware chunking.** Split on headings and keep the title path (doc > section > subsection) in each chunk. Keep runbook steps and tables intact. Each chunk records document, page or anchor, and version.
- **Raw copies and replay.** Keep the raw files, deduplicated by hash, so you can re-chunk or re-embed after a parser or model change without re-crawling.
- **Incremental, idempotent sync.** Re-index only changed documents. A second run with no source changes makes zero changes. Deleted or unpublished documents are removed from the index promptly.
- **Staleness alert.** Alert when the sync has not run on schedule, and when a document has not been reviewed past its review date.

## Retrieval

- **Filter by permission before ranking.** The user's groups go into the query as a hard filter, so restricted chunks are never retrieved, never sent to the model and never cited. Do not retrieve first and hide afterwards. The user's identity comes from SSO, never from anything the model or the request body supplies.
- **Hybrid search plus a reranker.** Combine keyword search (policy names, error codes and acronyms need exact matching) with embeddings, then rerank the top 30 to 50 down to about 6 to 8. Boost newer or "current" versions and demote superseded ones.

## Answering

- **Grounded answers with citations.** The assistant answers only from retrieved passages and cites document, section and last-updated date for every claim. If the evidence is weak or missing, it says "I couldn't find this" and names who owns the topic. It does not guess.
- **Documents are untrusted input.** Wiki text can contain instructions ("ignore previous rules"). Treat retrieved text strictly as data, and give the model no tools that write or send anything. This is a read-only assistant.
- **Existence of restricted material doesn't leak.** When someone asks about something they cannot access, the reply is the same as for a missing document ("no accessible source"), with an optional link to request access.

## Evaluation

- **Build a labelled set before launch.** Collect 100 to 150 real questions from Slack, helpdesk tickets and team leads. Each one has the expected source passages and a short reference answer. Include questions with no answer, outdated-version traps and cross-team access cases.
- **Measure retrieval separately from answers.** Track recall@k for retrieval, then faithfulness (is every claim supported by the cited passage?), correctness and correct refusals for the answer. A retrieval miss and a bad generation need different fixes.
- **Access-control tests are a hard gate.** Run a scripted test suite as users from different teams. Zero restricted chunks may appear in retrieval, answers or citations, including through paraphrase, follow-ups and injection attempts. A single failure blocks release.
- **Regression gate.** Version the prompt, embedding model and chunking settings. Any change must pass the eval set at the agreed threshold, and the previous version stays available for rollback.

## Rollout

- **Pilot first.** Start with 8 to 10 users across 2 to 3 teams, including one team with restricted documents, for about 2 weeks. Add thumbs up/down with a reason and a "wrong or outdated" report button that goes to the document owner.
- **Operate it.** Log per-call model, tokens, latency and cost with a per-user budget. Keep traces free of question and answer content by default, because they would otherwise become an unprotected copy of restricted documents. Keep an audit log of who accessed which document IDs. Review weekly the unanswered questions and the bad ratings. Add real failures to the eval set, and send content gaps to the doc owners.
- **Widen in stages.** Go to all 50 once pilot quality holds (for example, at least 90% of ratings useful and zero access incidents). Name an owner for the index, the eval set and the permission sync, and keep a kill switch that turns the assistant off without touching the source systems.
