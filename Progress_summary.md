## Phase 0 — Scaffolding & Architecture Docs ✅

**Built**: Repo structure (agents/, api/, ui/, pipelines/, infra/, observability/, docs/, tests/), .gitignore, full docs/architecture.md (Vision, Problem Statement, Functional/Non-Functional Requirements, High-Level Architecture, Components, Tech Justification, Roadmap).
**Challenge**: the architecture doc initially only contained a later-added section ("Known Limitations") — the original Vision/Problem Statement/etc. content had gone missing from the file.
**Resolved by**: reconstructing the full document from earlier conversation history and re-saving it properly.

## Phase 1 — Bronze/Silver/Gold Pipeline (Databricks) ✅

**Built**: Unity Catalog structure (aegis.bronze/silver/gold), 9 Bronze Delta tables (Olist e-commerce dataset) via a reusable ingest_to_bronze() function, 9 Silver tables (typed, validated), 1 Gold table (monthly_revenue, joined + aggregated).

**Challenges & fixes**:

**Table mix-up**: bronze.customers got accidentally overwritten with orders data due to notebook cells run out of order — fixed by re-running the correct ingestion call, added overwriteSchema=true to handle Delta's schema-mismatch protection.
**inferSchema risk**: learned to use explicit all-StringType() Bronze schemas instead of Spark's automatic type inference, to avoid silent/inconsistent type guessing.
CSV parsing corruption in order_reviews (embedded commas/quotes in review text misaligning columns) — worked around with try_cast/try_to_timestamp (suggested by Databricks' built-in AI assistant), documented as an unresolved root cause.
Integer columns (price, payment_value) initially truncated decimals — caught and fixed by re-ingesting as StringType() in Bronze, casting to double properly in Silver.
Designed the Gold monthly_revenue table from a real business question (revenue by month), reasoning through what "revenue" means, which date to group by, and which order statuses to include — validated the multi-payment-row join logic against real data before trusting the aggregation.

## Phase 2 — Ingestion Agent ✅ (with documented limitation)

**Built**: agents/ingestion_agent.py — Pydantic models (ColumnAnomaly, SchemaAssessment), tool functions (get_sample_rows, get_existing_schema), prompt builder, assess_schema() using Ollama's structured format parameter.
**Challenge**: empirically found the local 3B model (llama3.2) consistently hallucinates schema anomalies — flagging columns as "missing" or "new" even when they were genuinely present in the known schema, across 5+ test runs, with both the original and an improved, more structured prompt.
**Resolved by**: documenting this as a known limitation in docs/architecture.md, with human-in-the-loop review as the designed mitigation, and a deferred architectural fix identified (move exact list comparison to deterministic Python, reserve the LLM only for rename judgment).

## Phase 3 — RAG Agent ✅

**Built**: agents/rag_agent.py — document chunking (chunk_text), embedding + indexing (build_index, using Ollama's nomic-embed-text + FAISS), retrieval + generation (answer_question).

**Challenges & fixes**:

ChromaDB's .add() caused a persistent native-level crash (0xC0000005 access violation) on Windows — tried reinstalling dependencies and installing the VC++ Redistributable, neither resolved it — pivoted to FAISS instead, which worked immediately.
Real retrieval-quality bug: a newly added definitional sentence in architecture.md wasn't being retrieved even though it existed in the document, because it landed in a large, poorly-bounded chunk (mixed with an ASCII diagram) that didn't rank in the top-2 nearest results — fixed by increasing k (number of retrieved chunks) from 2 to 4, and identified chunk-boundary quality as a real, ongoing design concern.

## Phase 4 — Analytics Agent ✅ (core loop working)

**Built**: agents/analytics_agent.py — build_sql_prompt(), a self-designed is_safe_select_query() guardrail (allowlist: must start with SELECT, no chained statements), ask_analytics_agent() (Ollama structured SQL generation → safety check → real execution via databricks-sql-connector).

**Challenges & fixes**:

First real VS Code ↔ Databricks connection: set up SQL Warehouse credentials, personal access token, .env file, and databricks-sql-connector — validated with a direct test query before building agent logic on top.
Generated SQL initially dropped the aegis.gold. schema/catalog prefix from the table name (even though the prompt explicitly stated it), causing a TABLE_OR_VIEW_NOT_FOUND error — fixed via a stronger, more explicit prompt; a code-level .replace() safety net (just added above) provides a second, deterministic layer of protection against this recurring.

## Phase 5 — Monitoring/RCA Agent ✅ (core loop working)

**Built:** `agents/monitoring_agent.py` — two halves:
- **Monitoring (deterministic):** `w.jobs.list_runs()`, `w.jobs.get_run()`, `w.jobs.get_run_output()` via `databricks-sdk` to fetch real job status and detailed task-level error messages.
- **RCA (LLM-based):** `RootCauseAnalysis` Pydantic model, `build_rca_prompt()`, `diagnose_failure()` — Ollama structured output, same pattern as every other agent.

**Challenges & fixes:**
- Created a real, deliberately-failing Databricks Job (`TABLE_OR_VIEW_NOT_FOUND` error) to have genuine failure data to build and test against, instead of hypothetical error text.
- `get_run_output` initially failed with `InvalidParameterValue`, because it requires the **task-level** `run_id`, not the top-level job run's `run_id` — fixed by first calling `get_run()` to retrieve `tasks[0].run_id`, then passing that into `get_run_output()`.
- Repeated the class-nesting indentation bug from Phase 4 (functions accidentally defined inside `class RootCauseAnalysis(BaseModel):` instead of at file top-level) — now a recognized, named pattern to watch for going forward.

**Key finding:** unlike Phase 2's Ingestion Agent, which hallucinated even on clear-cut schema comparisons, this RCA agent gave an accurate, sensible diagnosis on the first real test — likely because the input error message was explicit and unambiguous, requiring summarization rather than inference over incomplete/implicit information. Reinforced later (Phase 6 integration testing) with a counterexample: the same agent, tested again through the live API, suggested a **non-existent CLI command** (`dbutil.rebuild_metastore()`) as a fix, while self-reporting `requires_human_review: false` — concrete evidence that agent-reported confidence/review flags cannot be trusted as a sole safeguard.

**Design decision made:** `requires_human_review` is agent-reported but not solely trusted — a system-enforced human-approval rule applies to all RCA-driven actions, regardless of the agent's self-assessed confidence, consistent with lessons from Phases 2 and 4.

**Deferred to Phase 7:** Prometheus/Grafana observability integration — belongs with broader infra/monitoring setup, not agent-specific logic.

## Phase 6 — FastAPI Orchestration + Streamlit UI ✅ (core done, polish deferred)

**Built:** `api/main.py` — FastAPI app with `/health`, `/rag/ask`, `/analytics/ask`, `/monitoring/diagnose`, `/ingestion/assess`, each backed by a Pydantic request model matching the underlying agent function's real parameters. `ui/app.py` — Streamlit UI with a live "API Online/Offline" health check and one interactive section per agent, each calling its FastAPI endpoint via `requests.post()` and displaying results.

**Challenges & fixes:**
- **Import side-effects:** importing agent modules (e.g., `from agents.rag_agent import ...`) was re-executing all their old top-level test/debug code on every FastAPI startup — causing real, unnecessary Ollama and Databricks API calls just from starting the server. Fixed across all 4 agent files using the `if __name__ == "__main__":` guard, a now-recognized standard Python pattern, keeping module-level setup (classes, functions, client initialization) outside the guard and test-only code inside it.
- **Repeated class-nesting indentation bug** (functions defined inside a Pydantic `class` body instead of at file top-level) — recurred in both `analytics_agent.py` and `monitoring_agent.py` during initial FastAPI wiring; now a recognized pattern to self-check for.
- **Ungraceful crash on bad input:** requesting `/ingestion/assess` with a non-existent file path caused an unhandled `FileNotFoundError`, producing a raw 500 error that broke the Streamlit UI with a `JSONDecodeError` instead of a clean message — identified as a real gap; try/except error handling across all 4 endpoints deferred as a known follow-up.
- **Dead code caught in review:** `analytics_agent.py`'s `.replace()` safety net (Phase 4) was computed as `corrected_query` but never actually used in the safety check or execution — fixed to actually apply the correction.

**Key finding, reinforced live through the UI:** the Monitoring agent suggested a fabricated, non-existent CLI command (`dbutil.rebuild_metastore()`) as a fix while self-reporting `requires_human_review: false` — and separately, the Ingestion agent hallucinated a false "renamed column" anomaly on an unmodified file, again with high self-reported confidence. Both reinforce the standing design decision: agent-reported confidence and review flags are not trusted as sole safeguards; human review is enforced by system design, not delegated to the agent.

**Deferred to later:** try/except error handling on all 4 endpoints; Approve/Reject buttons for Ingestion/Monitoring outputs (the fuller human-in-the-loop interaction); minor UI polish (`st.json()` instead of raw `st.write()`).

**Milestone reached:** all 4 agents are now accessible through one unified, working, browser-based application — Streamlit → FastAPI → Agents → Ollama/Databricks — the first point in the project where Aegis is a real, demoable product rather than a set of separate scripts.