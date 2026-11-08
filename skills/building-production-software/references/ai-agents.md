# AI and LLM features

Use when building an LLM agent, chatbot, tool-calling or RAG feature, choosing a model or provider, writing prompts, handling agent latency, cost or context limits, letting an AI change data.

## Checklist (read first)

- [ ] Side effects need server-verified human confirmation; adversarial phrase tests.
- [ ] Tool args validated server-side; refusals teach the fix; refuse→retry test.
- [ ] Provider chosen by quota × cost; ≤2 providers; per-call ledger; adapter.
- [ ] Own memory with token cap; stable prefix; cache hits measured.
- [ ] Latency targets; end-to-end profile; reproducible benchmark set.
- [ ] Tools as data contracts; instructions in tool descriptions.
- [ ] Figures grounded; verifier knows legitimate sources; user-facing template text.
- [ ] Server-side slots; eval set of real transcripts re-run on every prompt change.
- [ ] Tokens counted on all paths; semaphore, deadline, heartbeat, cancel.
- [ ] Content-free traces; injection tests; budgets owned.

## Rules

### 1. The model proposes, deterministic code decides
- Any action with side effects needs an explicit human confirmation verified by server code (allowlisted phrases + adversarial negative tests).
- Re-check permissions at execution time; pin one model per pending action; record which model proposed it.
- **Why:** LLM output is untrusted input, however good the model.
- **Real case:** Consent was once decided by a tool argument the model chose.
- **Look up:** Human-in-the-loop; prompt-injection resistance.

### 2. Recipe: an AI that changes data
- The tool never writes. It validates arguments and stores a pending action (proposal, base revision, proposing model, expiry) and shows old → new.
- The human confirms with a button carrying the pending-action id (preferred) or an allowlisted phrase; server code checks it, re-checks permissions and expiry.
- Execution calls the same guarded write function the UI uses (lock, re-check base revision → 409 if moved, supersede, audit with origin = agent_confirmed and the model name).
- Tests: model-chosen "confirm" argument refused, "yes" inside tool output refused, non-admin refused, stale base revision refused, two concurrent confirms → one write.
- **Why:** Each safety rule lives in a different layer; the recipe shows how they compose.
- **Real case:** Consent was once a model-chosen tool argument, and an unanchored regex accepted "I confirm nothing".
- **Look up:** Human-in-the-loop; pending-action pattern.

### 3. Validate tool arguments like any untrusted input
- Types, units and ranges checked on the server; prompts only help.
- Refusals tell the model what to send instead; test the refuse → retry loop as a scripted conversation.
- **Why:** The model will send 2.1 when you meant 0.021.
- **Real case:** Only a human's cancel stopped a 210%-a-month change.
- **Look up:** Tool-call validation.

### 4. Choose providers by quota and unit cost, behind an adapter
- Tokens per request × requests per minute vs the quota; cost per answer.
- ≤2 equivalent providers; no switching mid-turn or after a tool call; log provider/model/tokens/latency per call.
- Provider-neutral message types; each client serialises its own wire format.
- **Why:** Free tiers and rate limits decide feasibility before quality does.
- **Real case:** A free tier's 7,000 tokens/minute was shared by all users at ~4.5k tokens per question; the provider changed four times.
- **Look up:** Ports and adapters; unit economics.

### 5. Own the memory; stable prefix first
- Keep conversation memory in your own store with a token cap (recent turns verbatim + rolling summary + latest tool results).
- Order prompt content from never-changes to always-changes; keep the prefix byte-identical; measure cache hits.
- **Why:** Vendor-held state grows, is opaque and locks you in; prompt caching only works on stable prefixes.
- **Real case:** A vendor stored-chat feature grew to 24k tokens and was dropped after two weeks; the owned design ran at ~9k tokens with 99.9% cached prefix.
- **Look up:** Prompt caching; context compaction.

### 6. Profile before optimising
- Set a latency target per request type; profile one real request end to end; fix the biggest cost first.
- Keep a fixed benchmark set; publish reproducible before/after numbers.
- **Why:** Most "LLM latency" is your own code.
- **Real case:** 54.8 of 65 s was tool work (DB setup, 30k config reads, repeated rebuilds); fixes took a what-if from 25.5 s to 9.8 s.
- **Look up:** Amdahl's law; latency budgets.

### 7. Tools are data contracts
- One schema source (e.g. a Pydantic model); results are `{data, citations, tables}` — no prose aimed at the model.
- Let the model choose intent through explicit arguments, not regex over user text.
- Put instructions in the tool description, not the global system prompt.
- **Why:** Prose-filled tools can't be reused by other agents or MCP; global instructions tax every request.
- **Real case:** Feature-specific rules in the system prompt made every simple question pay for them.
- **Look up:** MCP-ready tools.

### 8. Ground every figure, with a precise verifier
- Every number in an answer traces to a tool result from this turn; verify (value, entity, period), not digits.
- List every legitimate source (tool results, user's own words, echoed inputs) so the verifier doesn't reject them.
- On rejection drop the bad figure; review rejections; your template text must be user-facing because the model copies it.
- **Why:** Too loose lets wrong numbers through; too strict creates loops and latency.
- **Real case:** A digit-only verifier passed the right value on the wrong month; later ~20 fixes tuned false rejections.
- **Look up:** Grounding; validator precision/recall.

### 9. Conversation state in code; evals from real transcripts
- Store slots (period, inputs, outputs) server-side and only overwrite them with new values.
- Encode "ask vs answer" as a small decision table, enforced in code where possible.
- Every bad real chat becomes a multi-turn regression test; re-run the eval set after every prompt change.
- **Why:** Prompt edits regress quietly.
- **Real case:** One what-if took five replies; a clarifying question was retuned four times.
- **Look up:** Dialogue state tracking; LLM evals.

### 10. Turns are bounded, accounted and cancellable
- Count tokens on every path including errors and disconnects; per-round and per-user budgets.
- Dedicated executor + semaphore (503 beyond); clients built once; turn deadline; SSE heartbeat; client AbortController.
- **Why:** Agents are long-running, expensive requests.
- **Real case:** Forty slow chats took /health down through a shared thread pool.
- **Look up:** Backpressure.

### 11. Privacy and budgets by default
- Traces exclude content unless a flag is set; rotate and retain; prompt-injection test suite.
- Token/size/latency budgets are tests; only the owner raises them, on the record.
- **Why:** Traces become a second, unprotected copy of every conversation.
- **Real case:** A trace file logged every prompt unbounded; a token budget was raised inside a test commit.
- **Look up:** Privacy by design; Goodhart's law.

