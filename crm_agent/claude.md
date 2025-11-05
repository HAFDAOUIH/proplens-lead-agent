### CRM Agent Roadmap (Quick‑wins style)

This plan breaks the challenge into small, verifiable steps (15–60 minutes each). Every mini goal has a Why, What, How, and a Done check.

## Current progress snapshot
- [x] Repo skeleton + health routes
- [x] JWT login + protected route
- [x] Leads foundation (Mini 1–3) ✅
  - [x] `Lead` model + migrations (`crm_id`, `country_code`, core fields)
  - [x] CRM .xlsx import API (header-aware; openpyxl; clear errors)
  - [x] Shortlist API with ≥2 filters rule; case-insensitive/substring logic
- [x] Vector/RAG base (Mini 1–2) ✅
  - [x] Embeddings + ChromaDB infrastructure
  - [x] Brochure upload + ingest pipeline (PDF extraction, OCR fallback, token-based chunking)
  - [x] Search API for semantic search over brochures
- [x] Vanna Text-to-SQL (Mini 1–3) ✅
  - [x] VannaClient initialization with Groq + ChromaDB
  - [x] SQL executor with safety validation
  - [x] DDL + 10 training examples seeded
  - [x] Query and seed API endpoints
- [x] RUNBOOK with comprehensive cURL scripts ✅

## 1) Leads foundation
- **Mini 1 — Create `Lead` model**
  - **Why**: Persist CRM rows for shortlist and analytics.
  - **What**: Model fields: `name, email, phone, unit_type, budget_min, budget_max, status, last_conversation_date, last_conversation_summary, project_enquired`.
  - **How**: Define in `crm_agent/core/models.py`, add app to `INSTALLED_APPS`, run migrations.
  - **Done**: Migrations apply; admin shows `Lead`.

- **Mini 2 — Import endpoint**
  - **Why**: Load the mock Excel once.
  - **What**: POST `/api/leads/import` accepts file upload or server path; inserts rows.
  - **How**: `crm_agent/ingestion/crm_loader.py` using `pandas.read_excel`; Ninja router `crm_agent/api/leads.py`.
  - **Done**: Response reports inserted count; DB shows rows.

- **Mini 3 — Shortlist endpoint with ≥2 filters**
  - **Why**: Core filtering per user story.
  - **What**: POST `/api/leads/shortlist` with optional filters (project_enquired, budget_min/max, unit_type[], status, date_from/date_to). Enforce at least 2 filters.
  - **How**: Validate payload; build Django queryset; return `{count, leads:[{id,name,email}]}`.
  - **Done**: Two filters → 200 with expected list; one filter → 400.

## 2) Vector/RAG base
- Status: planned, design approved. See classes below; implement next.
- **Mini 1 — Embeddings + Chroma wiring**
  - **Why**: Reusable RAG infra for brochures and Vanna training.
  - **What**: `all-MiniLM-L6-v2` embeddings; Chroma persisted under `crm_agent/data/chroma`.
  - **How**: `crm_agent/core/db.py` with `get_embeddings()` and `get_chroma_client(persist_dir)`.
  - **Done**: Debug util inserts 2 docs and retrieves the correct one.

- **Mini 2 — Brochure upload + ingest**
  - **Why**: Required ingestion API.
  - **What**: POST `/api/docs/upload` (1..n PDFs) → save to `data/brochures` → extract (pypdf fast‑path; OCR fallback w/ Tesseract for image pages) → chunk (~900 tokens, 100 overlap) → embed → upsert to Chroma.
  - **How**: OOP pipeline
    - `core/pipelines/document_ingestion.py`: `DocumentIngestor`
    - `core/pipelines/extractors.py`: `PdfExtractor` + `OcrExtractor`
    - `core/pipelines/chunking.py`: `TextChunker`
    - `core/embeddings.py`: `MiniLMEmbedder`
    - `core/vector_store.py`: `ChromaStore`
  - **Done**: Debug GET `/api/docs/search?q=amenities&project=Beachgate by Address` returns k≈4 relevant chunks with page refs.

## 3) Vanna Text‑to‑SQL ✅
- **Mini 1 — Initialize Vanna with Groq + Chroma**
  - **Why**: Meet T2SQL requirement without paid OpenAI.
  - **What**: Vanna uses Groq's OpenAI‑compatible API and Chroma corpus.
  - **How**: `crm_agent/agent/vanna_client.py` with `VannaClient` class (ChromaDB_VectorStore + OpenAI_Chat mixin), `crm_agent/agent/sql_executor.py` for safe execution.
  - **Done**: ✅ "How many leads total?" returns correct SQL and results. OpenAI proxies patch applied to fix compatibility issues.

- **Mini 2 — Seed DDL + examples**
  - **Why**: Improve SQL generation accuracy.
  - **What**: Add DB DDL and 10 NL→SQL examples (counts, filters, aggregations, date ranges).
  - **How**: `crm_agent/ingestion/vanna_seed.py` stores training items in Chroma via `VannaSeeder.seed()`.
  - **Done**: ✅ Seeded 1 DDL + 10 examples. Queries working perfectly: "Show all Connected leads", "Count leads by project", "List all unique project names", etc.

- **Mini 3 — T2SQL API endpoints**
  - **Why**: Expose natural language queries via REST API.
  - **What**: POST `/api/t2sql/query` (NL → SQL → results) and POST `/api/t2sql/seed` (training).
  - **How**: `crm_agent/api/t2sql.py` with `query_t2sql()` and `seed_vanna()` endpoints.
  - **Done**: ✅ Both endpoints working. Query endpoint returns SQL, rows, columns, summary. Safe execution (SELECT-only) enforced.

## 4) LangGraph router MVP
- **Mini 1 — Graph skeleton**
  - **Why**: Central decision point per requirement.
  - **What**: `crm_agent/agent/graph.py` with state `{query, intent, result, sources?}` and nodes `router`, `rag_answer`, `t2sql_answer`.
  - **How**: Simple keyword heuristic for router; call RAG/T2SQL tools.
  - **Done**: `/api/agent/query` routes: brochure Q → RAG; analytics Q → T2SQL.

- **Mini 2 — RAG answer tool**
  - **Why**: Grounded answers from brochures.
  - **What**: `crm_agent/agent/tools_rag.py` `answer(query, project?) -> {answer, sources}`.
  - **How**: Chroma similarity search k=4; concise answer 120–150 words; include sources.
  - **Done**: Amenity Q returns grounded answer with 2–4 sources.

## 5) Campaigns + messaging ✅
- **Mini 1 — Models** ✅
  - **Why**: Track campaigns and conversations.
  - **What**: `Campaign`, `Message`, `Thread`, `ThreadMessage` in `coreapp/models.py`.
  - **How**: Define models; migrate.
  - **Done**: ✅ Tables exist; migration applied.

- **Mini 2 — Create campaign + generate emails** ✅
  - **Why**: Hyper‑personalized outreach.
  - **What**: POST `/api/campaigns` with `{project, channel, offer_text, lead_ids[]}`; generate body using lead profile + top brochure chunks + offer; mock send.
  - **How**: `core/campaign_service.py` builds prompts with RAG + LLM; `api/campaigns.py` handles API.
  - **Done**: ✅ Response `{sent_count, sample_messages}`; DB rows inserted. AI generates personalized subject + 200-250 word body.

- **Mini 3 — Reply simulation → agent** ✅
  - **Why**: Handle follow‑ups via router.
  - **What**: POST `/api/campaigns/{id}/lead/{lead_id}/reply` stores lead message and agent answer; GET `/api/campaigns/{id}/followups` lists threads.
  - **How**: Save `ThreadMessage(role="lead")`, call graph with config, save agent reply.
  - **Done**: ✅ RAG/T2SQL/Clarify responses stored; followups endpoint shows thread with recent messages.

## 6) Metrics + dashboard endpoints ✅
- **Mini 1 — Metrics** ✅
  - **Why**: Demonstrate KPIs.
  - **What**: GET `/api/campaigns/{id}/metrics` → `leads_shortlisted, messages_sent, unique_leads_responded, goals_achieved_count`.
  - **How**: Aggregate queries on models.
  - **Done**: ✅ Fully implemented; returns all KPIs.

- **Mini 2 — Goals list**
  - **Why**: “Followups” screen.
  - **What**: GET `/api/campaigns/{id}/goals` → list with `name, contact, last summary, proposed date`.
  - **How**: Query `Thread`/`ThreadMessage`.
  - **Done**: Returns expected shape.

## 7) Tests + evaluation
- **Mini 1 — Pytest basics**
  - **Why**: Prevent regressions; matches spec.
  - **What**: `tests/test_leads.py`, `test_rag.py`, `test_t2sql.py`, `test_e2e.py`.
  - **How**: Django test client; seed temp DB and small PDF.
  - **Done**: `pytest -q` passes.

- **Mini 2 — DeepEval**
  - **Why**: LLM quality checks; JSON artifact required.
  - **What**: `tests/run_eval.py` runs faithfulness + relevance; writes `agent_evaluation_scores.json`.
  - **How**: Use retrieved chunks and example queries.
  - **Done**: JSON created and committed.

## 8) Deploy + README
- **Mini 1 — Prod settings / env**
  - **Why**: Enable hosted demo.
  - **What**: `.env.example` complete; optional prod flag.
  - **How**: Configure `ALLOWED_HOSTS`, keys, and start command.
  - **Done**: Local prod boot OK.

- **Mini 2 — Deploy (Render/Fly)**
  - **Why**: Share live URL.
  - **What**: Start: `uvicorn app.asgi:application --host 0.0.0.0 --port $PORT`; persistent disk for Chroma.
  - **How**: Provision service; set env vars.
  - **Done**: `/api/health` works on live URL.

- **Mini 3 — README**
  - **Why**: Reviewer guidance.
  - **What**: How to run locally, seed CRM, upload brochures; API list with cURL; auth; architecture; LangGraph routing; live link; sample creds.
  - **Done**: Reviewer can reproduce E2E in ≤10 minutes.


