### CRM Agent – Runbook (Quick Wins Progress + Test Commands)

This file tracks what's DONE so far and gives copy‑pasteable commands to verify each step locally.

## Stack
- Framework: Django + Django Ninja
- Auth: JWT (SimpleJWT)
- DB: SQLite (dev)
- Vector Store: ChromaDB (embedded, persistent)
- Embeddings: all-MiniLM-L6-v2 (Sentence Transformers)
- Import: pandas + openpyxl
- PDF Processing: pypdf + pytesseract (OCR fallback)

## Status

### Leads foundation ✅
- [x] Project skeleton and health endpoints
- [x] JWT login + protected route
- [x] Django app `coreapp` with `Lead` model
  - Fields: `crm_id, name, email, country_code, phone, unit_type, budget_min, budget_max, status, last_conversation_date, last_conversation_summary, project_enquired`
- [x] CRM Excel import API (validates .xlsx, uses openpyxl)
- [x] Shortlist API with rule: at least 2 filters
  - Case‑insensitive matching for `status`
  - Substring OR matching for `unit_type` (e.g., "2 bed" matches variants)

### Text-to-SQL ✅
- [x] Vanna client (`VannaClient` using Groq + ChromaDB)
  - Mixin pattern: ChromaDB_VectorStore + OpenAI_Chat
  - Groq API configured as OpenAI-compatible endpoint
  - Separate ChromaDB collection for training data
- [x] SQL executor (`SQLExecutor` with safety validation)
  - SELECT-only queries allowed
  - Blocks dangerous keywords (DROP, DELETE, etc.)
  - Parameterized execution via Django ORM
- [x] Vanna seeder (`VannaSeeder`)
  - Auto-generates DDL from Lead model
  - 10 NL→SQL training examples (counts, filters, aggregations)
- [x] T2SQL API endpoints
  - POST `/api/t2sql/query` → Natural language → SQL → results
  - POST `/api/t2sql/seed` → Seed training data

### Vector/RAG base ✅
- [x] Embeddings infrastructure (`MiniLMEmbedder` using Sentence Transformers)
- [x] ChromaDB persistent storage (`ChromaStore` with `PersistentClient`)
- [x] PDF extraction pipeline (`PdfExtractor` with OCR fallback)
  - Fast-path: `pypdf` for text-layer PDFs
  - OCR fallback: `pytesseract` for image-heavy pages (< 200 chars)
  - Text normalization: handles soft hyphens, hyphen-line breaks
- [x] Token-based chunking (`TextChunker` using `tiktoken` GPT-2 tokenizer)
  - Target: 500 tokens per chunk
  - Overlap: 50 tokens for context continuity
  - Accurate token counting (not word approximation)
- [x] Document ingestion pipeline (`DocumentIngestor`)
  - Content-hash deduplication
  - End-to-end: PDF → pages → chunks → embeddings → ChromaDB
- [x] Brochure upload API (`POST /api/docs/upload`)
  - Accepts 1..n PDFs
  - Requires `project` param or PDF Title metadata
  - Stores by content hash (idempotent)
  - Returns: `inserted_chunks`, `pages_processed`, `ocr_pages`
- [x] Search API (`GET /api/docs/search`)
  - Semantic search over ingested brochures
  - Optional `project` filter
  - Returns: `matches` with text, metadata, distance scores
- [x] Debug endpoint (`GET /api/docs/count`)
  - Returns total chunks in ChromaDB collection

## How to run (local)
```bash
source /home/hafdaoui/Documents/Proplens/.venv/bin/activate
pip install -r /home/hafdaoui/Documents/Proplens/crm_agent/requirements.txt

cd /home/hafdaoui/Documents/Proplens/crm_agent/app
python manage.py migrate
python manage.py createsuperuser  # if needed for login
uvicorn app.asgi:application --reload --host 0.0.0.0 --port 8000
```

## Endpoints

### Auth & Health
- POST `/api/login` → `{ access }`
- GET `/api/health` → quick check
- GET `/api/health-protected` → requires `Authorization: Bearer <JWT>`

### Leads
- POST `/api/leads/import` → form‑data `file=@*.xlsx`
- POST `/api/leads/shortlist` → JSON body; must include ≥2 filters

### Brochures/Documents
- POST `/api/docs/upload` → form‑data `files=@*.pdf`, query: `project=...&force=true|false`
- GET `/api/docs/search` → query: `q=...&k=4&project=...` (project optional)
- GET `/api/docs/count` → returns `{total_chunks: N}`

### Text-to-SQL
- POST `/api/t2sql/query` → JSON body: `{question: "..."}`
- POST `/api/t2sql/seed` → Seed Vanna with DDL and examples (run once)

### Shortlist filters (all optional individually, but pick ≥2)
- `project_enquired: str`
- `budget_min: number`, `budget_max: number`
- `unit_type: [str, ...]` (substring, case‑insensitive)
- `status: str` (case‑insensitive)
- `date_from: YYYY-MM-DD`, `date_to: YYYY-MM-DD`

## cURL test script (copy/paste)
Set your token and file path first.
```bash
BASE="http://127.0.0.1:8000"
TOKEN="<PASTE_YOUR_ACCESS_TOKEN>"
EXCEL="/home/hafdaoui/Documents/Proplens/AI Engineer Challenge/Proplens AI Engineer_Challenge/Mock CRM leads for nurturing.xlsx"

echo "Health public:" && curl -s "$BASE/api/health" | jq

echo "Health protected (401 expected without token):" && curl -s -i "$BASE/api/health-protected" | head -n 1
echo "Health protected (200 with token):" && curl -s "$BASE/api/health-protected" -H "Authorization: Bearer $TOKEN" | jq

echo "Import leads (.xlsx) > 0 rows:" && \
curl -s -X POST "$BASE/api/leads/import" -H "Authorization: Bearer $TOKEN" -F "file=@$EXCEL" | jq

echo "Shortlist guard (expect 400):" && \
curl -s -X POST "$BASE/api/leads/shortlist" -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"status":"Connected"}' | jq

echo "Shortlist by project + status:" && \
curl -s -X POST "$BASE/api/leads/shortlist" -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"project_enquired":"gate","status":"Connected"}' | jq

echo "Shortlist by unit type + status:" && \
curl -s -X POST "$BASE/api/leads/shortlist" -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"unit_type":["2 bed"],"status":"Connected"}' | jq

echo "Shortlist with budget_min:" && \
curl -s -X POST "$BASE/api/leads/shortlist" -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"unit_type":["2 bed"],"status":"Connected","budget_min":1200000}' | jq

echo "Shortlist date range example:" && \
curl -s -X POST "$BASE/api/leads/shortlist" -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"status":"Connected","date_from":"2023-01-01","date_to":"2024-12-31"}' | jq
```

## Test Commands (Brochures)

```bash
BASE="http://127.0.0.1:8000"
TOKEN="<PASTE_YOUR_ACCESS_TOKEN>"
PDF_PATH="/home/hafdaoui/Documents/Proplens/AI Engineer Challenge/Proplens AI Engineer_Challenge/Project brochure dataset/DLF West Park details.pdf"

# Upload brochure
curl -X POST "$BASE/api/docs/upload?project=DLF%20West%20Park&force=true" \
  -H "Authorization: Bearer $TOKEN" \
  -F "files=@$PDF_PATH" | jq

# Check chunk count
curl -s "$BASE/api/docs/count" \
  -H "Authorization: Bearer $TOKEN" | jq

# Search (with project filter)
curl -s "$BASE/api/docs/search?q=west%20park&k=4&project=DLF%20West%20Park" \
  -H "Authorization: Bearer $TOKEN" | jq

# Search (without project filter - use empty project=)
curl -s "$BASE/api/docs/search?q=amenities&k=4&project=" \
  -H "Authorization: Bearer $TOKEN" | jq
```

## Known behaviors
- Import is idempotent in the sense that it won't error on re‑upload, but duplicates can occur (no dedupe yet).
- `unit_type` uses `icontains` so variants like "2 Bed" / "2-bedroom" are matched.
- Budget logic: `budget_max >= budget_min_filter` and `budget_min <= budget_max_filter` when provided.
- Brochure upload uses content hash (SHA256) for idempotence - same file = same hash = reused.
- OCR fallback triggers automatically if text layer has < 200 chars per page.
- Chunking uses tiktoken (GPT-2 tokenizer) for accurate token counting (500 tokens target, 50 overlap).

## Test Commands (Text-to-SQL)

```bash
BASE="http://127.0.0.1:8000"
TOKEN="<PASTE_YOUR_ACCESS_TOKEN>"

# 1. First, seed Vanna with DDL and examples (run once after deployment)
# This stores: 1 DDL (schema) + 10 question-SQL pairs in ChromaDB
curl -X POST "$BASE/api/t2sql/seed" \
  -H "Authorization: Bearer $TOKEN" | jq
# Expected: {"message": "Vanna seeded successfully", "ddl_items": 1, "sql_examples": 10}

# 2. Test queries (similar to seeded examples - should work well)
echo "=== Test: Count total leads ==="
curl -X POST "$BASE/api/t2sql/query" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question": "How many leads total?"}' | jq

echo "=== Test: Show Connected leads ==="
curl -X POST "$BASE/api/t2sql/query" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question": "Show all Connected leads"}' | jq

echo "=== Test: Count by project ==="
curl -X POST "$BASE/api/t2sql/query" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question": "Count leads by project"}' | jq

echo "=== Test: Budget filter ==="
curl -X POST "$BASE/api/t2sql/query" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question": "Leads with budget over 1 million"}' | jq

# 3. New queries (Vanna will generalize from training data)
echo "=== Test: Average budget ==="
curl -X POST "$BASE/api/t2sql/query" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the average budget_min?"}' | jq

echo "=== Test: Filter by unit type ==="
curl -X POST "$BASE/api/t2sql/query" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question": "Show leads with 2 Bed units"}' | jq

echo "=== Test: Distinct values ==="
curl -X POST "$BASE/api/t2sql/query" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question": "List all unique project names"}' | jq

echo "=== Test: Group by status ==="
curl -X POST "$BASE/api/t2sql/query" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question": "How many leads by status?"}' | jq
```

**How Vanna Works:**
- Uses RAG (Retrieval-Augmented Generation): Searches ChromaDB for similar questions/examples
- Retrieves context: DDL (schema) + relevant question-SQL pairs
- LLM (Groq) generates SQL using retrieved context
- Safe execution: Only SELECT queries allowed (validated by SQLExecutor)

**Training Data (from seeding):**
- **DDL**: Database schema for `coreapp_lead` table
- **10 Examples**: Cover COUNT, WHERE, GROUP BY, LIKE, date filtering, NULL handling, ORDER BY + LIMIT

## Next goals (planned)
1) ✅ Brochure upload + ingest to Chroma (RAG store) - **DONE**
2) ✅ Vanna T2SQL init + seed examples - **DONE**
   - VannaClient with Groq + ChromaDB ✅
   - SQL executor with safety validation ✅
   - DDL + 10 training examples seeded ✅
   - Query endpoint working perfectly ✅
3) **LangGraph router MVP** (RAG vs T2SQL) - **NEXT**
   - Intent detection: brochure questions → RAG, analytics → T2SQL
   - Graph state management
   - Unified `/api/agent/query` endpoint
4) Campaign creation + personalized email generation
5) Handle customer replies with AI agent
6) Metrics and dashboard endpoints


