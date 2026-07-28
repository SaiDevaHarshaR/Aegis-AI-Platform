# Aegis AI Platform — Architecture

## 1. Product Vision

Aegis is an autonomous AI platform where specialized agents handle the full 
lifecycle of enterprise data and infrastructure operations — starting with 
Data Engineers, who get agents that ingest, validate, and pipeline raw data 
through Bronze/Silver/Gold layers instead of building it by hand, and 
extending to Platform Teams (automated infra monitoring and root-cause 
diagnosis) and Analysts (trustworthy SQL analytics and RAG-based knowledge 
search) built on that same clean data foundation.

## 2. Problem Statement

Enterprise data engineering today relies on manually-written, rule-based 
pipelines that break silently whenever reality drifts from what the author 
anticipated (renamed columns, changed types, unexpected nulls) — requiring 
a human to notice, investigate, and patch code by hand, which doesn't scale 
as data volume and system complexity grow. Aegis replaces the 
judgment-requiring parts of this workflow (schema matching, quality 
assessment, failure diagnosis) with specialized AI agents that reason over 
novel situations and explain their decisions, while keeping the 
deterministic, repeatable parts (data movement, SQL execution, Delta 
writes) as regular reliable code.

## 3. Functional Requirements

**Ingestion/Pipeline Agent:**
- Detect schema of newly ingested files and compare against existing Silver table schemas.
- Flag column-level anomalies (renamed columns, type mismatches, unexpected null rates) with a confidence score and human-readable explanation.
- Auto-route validated data through Bronze → Silver → Gold Delta Lake tables once schema is confirmed.

**Knowledge/RAG Agent:**
- Ingest documents (runbooks, schemas, past incident notes) into a vector store.
- Answer natural-language questions with cited sources.
- Refuse/flag when it doesn't have enough context.

**Analytics Agent:**
- Convert natural-language questions into SQL against Gold tables.
- Execute via Databricks SQL Warehouse, return results and explain query logic.

**Infra Monitoring/RCA Agent:**
- Watch job/pipeline run status, detect failures.
- Correlate against logs/metrics, propose root cause and suggested fix.
- Escalate to human if confidence is low.

## 4. Non-Functional Requirements

- **Explainability:** every agent decision includes a human-readable reason, not a black box.
- **Human-in-the-loop:** agents propose, humans approve high-impact actions.
- **Observability:** every agent action, tool call, and decision is logged/traceable (Prometheus/Grafana).
- **Local-first/cost-zero:** runs entirely on Ollama (CPU) + Docker Desktop + Databricks Free Edition, no paid APIs.
- **Reproducibility:** infra as code (Terraform), CI/CD (GitHub Actions).

## 5. High-Level Architecture

Data Sources are ingested by the Ingestion Agent into Bronze (Delta), then 
go to Silver (Delta, validated) for cleaning and processing, and finally 
to Gold (Delta, analytics-ready). Gold-layer structured data is used by 
the Analytics Agent; documents (runbooks, wikis, past incidents) are 
retrieved by the RAG Agent. The Monitoring Agent observes infrastructure 
via Prometheus and Grafana. Unity Catalog governs all layers. A FastAPI 
orchestration layer connects agents to a Streamlit UI for human review.
**Layer definitions:** Bronze stores raw, unmodified data exactly as ingested from source files. Silver contains cleaned, validated, and correctly-typed data with quality rules applied. Gold contains business-level, aggregated data shaped for direct analytics consumption.
Data Sources → Ingestion Agent → Bronze (Delta)
→ Silver (Delta, validated)
→ Gold (Delta, analytics-ready)
↓
┌───────────────┬───────────────┼───────────────┐
RAG Agent Analytics Agent Monitoring Agent (Unity Catalog governs all)
(vector DB) (SQL Warehouse) (Prometheus/Grafana)
└───────────────┴───────────────┴───────────────┘
FastAPI (agent orchestration layer)
Streamlit (human UI: review/approve agent actions)
Docker/K8s (deployment) + Terraform (infra) + GH Actions (CI/CD)

## 6. Major Components

1. Orchestration layer (FastAPI) — routes requests to the right agent, manages tool access.
2. Four specialized agents (Ingestion, RAG, Analytics, Monitoring/RCA).
3. Databricks layer (Bronze/Silver/Gold, Unity Catalog, SQL Warehouse, Lakeflow Jobs).
4. Vector store (for RAG).
5. Observability stack (Prometheus/Grafana + structured agent logs).
6. UI (Streamlit — human review/approval dashboard).
7. Infra/deploy (Docker → Kubernetes, Terraform, GitHub Actions).

## 7. Technology Justification

- **Ollama (CPU):** zero-cost local inference, forces engineering around small-model limits.
- **FastAPI:** async, typed, standard for serving agent/tool endpoints.
- **Databricks Free Edition:** real enterprise lakehouse experience without cost.
- **Kubernetes:** demonstrates operating agents as production services, not just scripts.
- **Terraform:** infra reproducibility.

## 8. Development Roadmap

1. Phase 0 — repo scaffolding, local dev environment.
2. Phase 1 — Ingestion + Bronze/Silver/Gold pipeline (no agent).
3. Phase 2 — Ingestion Agent (LLM-based schema/quality judgment).
4. Phase 3 — RAG Agent + vector store.
5. Phase 4 — Analytics Agent (NL→SQL).
6. Phase 5 — Monitoring/RCA Agent + Prometheus/Grafana.
7. Phase 6 — FastAPI orchestration + Streamlit UI.
8. Phase 7 — Kubernetes + Terraform + GitHub Actions.