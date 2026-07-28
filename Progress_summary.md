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