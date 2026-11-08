# Internal Q&A Assistant: Plan

## Ingestion
- Inventory sources first: count PDFs and wiki pages, record owner, team, last-updated date, and access group for each.
- Store the access group as metadata on every source document at ingestion. Treat a missing or unknown group as restricted, not public.
- Extract text per source type: native-text PDFs with a PDF parser, scanned PDFs with OCR, wiki pages via API or HTML export. Keep page numbers and section headings.
- Chunk by section (about 300 to 600 tokens with a small overlap), and carry the title, path, team, and page number on each chunk.
- Re-ingest on a schedule and on change events, and remove chunks when a source is deleted or its permissions change.

## Retrieval
- Enforce permissions in the retrieval query itself (a filter on the user's groups), never by filtering answers after generation.
- Combine keyword search (BM25) with vector search, then rerank the top results with a cross-encoder or a reranking model.
- Retrieve a small set of chunks (about 5 to 8) and pass only those to the model, with source IDs attached.

## Answering
- Ground every answer in retrieved chunks, cite document title and page or section for each claim, and link to the source.
- When retrieval finds nothing the user may see, say the answer is not available to them. Do not reveal that a restricted document exists.
- Refuse or defer on questions that need a human decision, such as policy exceptions, and say who to ask.
- Show the date each cited source was last updated, so stale policies are visible.

## Evaluation
- Build a test set of about 150 to 200 real questions from the team, with expected source documents, and include permission-boundary tests (a user must not see restricted answers).
- Measure retrieval recall at the top 8, citation accuracy, answer correctness (human-graded on a sample), and refusal rate on out-of-scope questions.
- Run the permission tests on every change to ingestion or retrieval, and treat any leak as a release blocker.

## Rollout
- Start with a pilot of about 10 employees across two or three teams, and collect thumbs-up or thumbs-down feedback with the chosen source.
- Expand to all 50 users once recall and citation accuracy meet agreed thresholds on the test set and the pilot shows no permission leaks.
- Log queries and answers for audit and improvement, with a retention limit and access restricted to admins.
