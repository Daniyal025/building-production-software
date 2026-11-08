# Internal Q&A assistant: plan (about 50 users, ~2,000 documents)

Scale is small: one Postgres with pgvector plus built-in full-text search is enough. No separate vector database, no agent framework. The one non-negotiable is that restricted documents never reach someone who shouldn't see them.

## Ingestion
1. **Connectors per source, run on a schedule plus change webhooks.** Pull PDFs and wiki pages with their source URL, title, last-modified date, owner and ACL. Re-ingest only changed documents (content hash). Nightly full reconcile catches deletes and moves.
2. **Store the access list with every document and every chunk** (team or group IDs copied from the source system, not hand-maintained). A document with no ACL information is treated as restricted and flagged. It is never treated as public.
3. **Parse by structure.** Split wiki pages by heading and PDFs by section. Keep tables and runbook step lists intact. Prepend the title and heading path to each chunk (about 300-500 tokens each). Scanned or garbled PDFs get OCR or are reported as failed.
4. **Failures are visible.** Keep a per-document status (ingested, failed, empty extraction) and a report of anything that didn't parse. A silently skipped document looks like "the policy doesn't exist."
5. **Handle staleness and duplicates.** Store modified dates and supersession (old vs new policy version). Dedupe near-identical copies. Show the document date in answers.

## Retrieval
6. **Enforce permissions in the retrieval query itself.** Filter by the asking user's groups (from SSO) before ranking, not after generation. Re-check group membership on every request. Never put restricted text in a shared cache, shared prompt prefix or shared summary.
7. **Hybrid search:** keyword (BM25/full-text) plus embeddings, merged, then a reranker over the top ~30 to pick about 6 chunks. Keyword search matters here because runbooks and product docs are full of exact names, error codes and acronyms.
8. **Optional metadata filters** (team, doc type, recency). Fetch neighbouring chunks when a hit is a step in a procedure.

## Answering
9. **Answer only from retrieved passages, with citations** (document title, section, link, date) on every claim. If retrieval is weak, say "I couldn't find this in the documents" and name the closest sources. Never fill the gap from the model's general knowledge.
10. **Don't leak the existence of restricted material.** When the best answer sits in a document the user can't see, reply with "not found in documents you can access", or point them to the owning team. Don't hint at its content or title.
11. **Treat document text as untrusted input.** Wiki pages can contain instructions. The assistant is read-only with no tools that write or send anything, and the prompt says retrieved text is data.
12. **Log without hoarding.** Per request, record user, retrieved chunk IDs, model and prompt version, tokens and latency. Keep question and answer text out of general logs, because they contain restricted content. Set a retention period. Add a per-user rate limit and cost cap.
13. **Thumbs up/down plus "wrong or outdated" on every answer**, routed to the document owner as well as the builders.

## Evaluation
14. **Build a labelled set of about 150 real questions** collected from employees, support channels and doc owners. Each has the expected source document(s) and a reference answer. Include unanswerable questions and ones where the right answer is "that's restricted to you."
15. **Measure retrieval and answer quality separately.** Retrieval: recall@k on the expected document. Answer: faithfulness to the cited passages, correctness, and correct refusals. Set pass thresholds up front.
16. **Permission tests are a hard gate with zero tolerance.** For each restricted document, run questions as users with and without access. Any leak fails the build. Also test group removal (access revoked means answers stop immediately) and prompt-injection attempts.
17. **Re-run the whole set on every change** to the chunking, embedding model, reranker, prompt or LLM. A change ships only if it meets the thresholds, and the previous version stays available for rollback.

## Rollout
18. **Phase 1: shadow and pilot.** Run it with 5-8 people across different teams, including at least one restricted-content team, for 2 weeks. Review every thumbs-down and every "not found." Fix documents and retrieval before widening.
19. **Phase 2: all 50, behind company SSO,** after the permission tests have passed against the real ACLs and a security or IT owner has signed off. Include a short note on what the assistant can't do (no legal or HR rulings, and always check the cited source).
20. **Operate it.** Name an owner. Track weekly answer rate, thumbs-down rate, top unanswered questions (these show documentation gaps) and ingestion failures. Alert on a stalled sync. Re-baseline the eval set quarterly with new real questions.

## Decisions to make early
- **Where the LLM runs.** Confirm that sending restricted content to a hosted model API is acceptable to your data policy, and that the provider doesn't retain or train on it. If not, use a self-hosted or private-endpoint model.
- **Source of truth for ACLs.** If the wiki and the PDF share have different group systems, map both to one identity group list before ingestion starts.
