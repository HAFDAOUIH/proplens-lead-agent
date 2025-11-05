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

## Test Commands (Agent Router) ✅

**IMPORTANT**: Always include `-H "Accept: application/json"` header to avoid content negotiation overhead!

```bash
BASE="http://127.0.0.1:8000"
TOKEN="<PASTE_YOUR_ACCESS_TOKEN>"

echo "=== Agent: brochure question routes to RAG ==="
curl -s -X POST "$BASE/api/agent/query" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{"question": "What amenities does Beachgate by Address include?"}' | jq

echo "=== Agent: analytics question routes to T2SQL ==="
curl -s -X POST "$BASE/api/agent/query" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{"question": "How many leads by status?"}' | jq

echo "=== Agent: low confidence triggers clarify ==="
curl -s -X POST "$BASE/api/agent/query" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{"question": "What about that thing?"}' | jq

echo "=== Agent: conversation continuity ==="
# First query
RESPONSE=$(curl -s -X POST "$BASE/api/agent/query" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{"question": "What properties are available?"}')

# Extract thread_id
THREAD_ID=$(echo $RESPONSE | jq -r '.thread_id')
echo "Thread ID: $THREAD_ID"

# Follow-up query in same conversation
curl -s -X POST "$BASE/api/agent/query" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d "{\"question\": \"Tell me more about the first one\", \"thread_id\": \"$THREAD_ID\"}" | jq
```

### Agent Router Features ✅

1. **Intelligent Routing** (November 2025)
   - Uses Groq LLM (llama-3.3-70b-versatile) to classify queries
   - Routes: `rag` (properties), `t2sql` (analytics), `clarify` (low confidence)
   - Returns confidence scores and reasoning

2. **Low-Confidence Handling** ✅
   - Queries with confidence < 0.6 trigger `clarify` route
   - Asks users to clarify intent instead of guessing
   - Improves UX by avoiding incorrect responses

3. **RAG Summarization** ✅
   - Retrieves relevant chunks from ChromaDB
   - Summarizes context using Groq LLM for concise answers (max 300 tokens)
   - Returns source citations with project, page, file, and distance score
   - Can be toggled via `summarize=False` parameter

4. **Conversation Memory** ✅
   - Uses LangGraph checkpointer with SQLite backend
   - Maintains conversation state across requests via `thread_id`
   - Enables follow-up questions and context retention
   - Auto-generates thread_id if not provided

5. **Metadata Improvements** ✅
   - Sources now include `project_name`, `page`, `source` file, and `distance` score
   - Properly extracts project metadata from ingested documents
   - No more `null` values in source citations

### Agent Response Schema

**RAG Route:**
```json
{
  "query": "What amenities does Beachgate by Address include?",
  "route": "rag",
  "intent": "The question asks about amenities...",
  "confidence": 0.9,
  "answer": "Beachgate By Address includes: 1) 1.5 KM pristine beach, 2) Panoramic sea/marina views, 3) Licensed restaurants nearby, 4) Marina and yacht club access, 5) 2 neighborhood parks, 6) Direct Sheikh Zayed Road access. These amenities provide cosmopolitan living with luxury seaside lifestyle.",
  "sources": [
    {
      "project": "Beachgate by Address",
      "page": 4,
      "source": "beachgate_brochure.pdf",
      "distance": 0.808,
      "similarity": 0.596
    }
  ],
  "thread_id": "6f64ba45-c8c4-48c3-9aae-e8f781f41a39"
}
```

**Note**:
- Answer is now concise (~150 words)
- `similarity` score added (0-1, higher is better)
- `project` is never null (shows "Unknown" if missing)

**T2SQL Route:**
```json
{
  "query": "How many leads by status?",
  "route": "t2sql",
  "intent": "The question is asking for a count...",
  "confidence": 1.0,
  "sql": "SELECT status, COUNT(*) as count FROM coreapp_lead GROUP BY status",
  "rows": [
    {"status": "new", "count": 45},
    {"status": "contacted", "count": 23}
  ],
  "columns": ["status", "count"],
  "thread_id": "9d79b7ad-6c2d-45ab-8e7b-905ea0cfb202"
}
```

**Clarify Route:**
```json
{
  "query": "What about that thing?",
  "route": "clarify",
  "intent": "Router error: low confidence...",
  "confidence": 0.4,
  "answer": "I'm not quite sure how to best answer your question...",
  "thread_id": "abc123"
}
```

## Configuration Options

### RAG Summarization
Edit `crm_agent/agent/graph.py`:
```python
# Disable summarization (return raw chunks)
rag_tool = RagTool(chroma_dir=CHROMA_DIR, summarize=False)

# Enable with custom model (faster/cheaper)
rag_tool = RagTool(
    chroma_dir=CHROMA_DIR,
    summarize=True,
    model="llama-3.1-8b-instant"
)
```

### Confidence Threshold
Edit `crm_agent/agent/graph.py` line 66:
```python
# Default: clarify if confidence < 0.6
if state.confidence and state.confidence < 0.6:
    return "clarify"

# More conservative: clarify if confidence < 0.7
if state.confidence and state.confidence < 0.7:
    return "clarify"
```

## Recent Fixes (November 2025) ✅

1. **LangGraph Checkpointer** - Fixed thread_id requirement
   - Issue: `ValueError: Checkpointer requires thread_id`
   - Fix: Added config parameter with thread_id when invoking graph
   - File: `crm_agent/api/agent.py`

2. **SqliteSaver Initialization** - Fixed connection object requirement
   - Issue: `'str' object has no attribute 'executescript'`
   - Fix: Pass SQLite connection object instead of string path
   - File: `crm_agent/agent/graph.py`

3. **Environment Variables** - Added .env loading
   - Issue: GROQ_API_KEY not loaded, empty LLM responses
   - Fix: Added `load_dotenv()` in Django settings.py
   - File: `crm_agent/app/app/settings.py`

4. **Router JSON Parsing** - Fixed Pydantic validation
   - Issue: Groq returns `reasons` as list, not string
   - Fix: Added field_validator to convert list to string
   - File: `crm_agent/agent/router.py`

5. **Markdown JSON Extraction** - Handle code blocks
   - Issue: LLM wraps JSON in markdown code blocks
   - Fix: Extract JSON from ```json or ``` blocks before parsing
   - File: `crm_agent/agent/router.py`

6. **Context-Aware Clarify Messages** - Smart follow-up detection
   - Issue: Vague follow-ups like "Tell me more" trigger clarify
   - Fix: Detect short/vague queries and provide helpful examples
   - File: `crm_agent/agent/graph.py`

7. **Conversation History in Router** - Better context understanding
   - Issue: Router doesn't know about previous queries
   - Fix: Pass last 3 queries to router for context-aware routing
   - Files: `crm_agent/agent/state.py`, `crm_agent/agent/router.py`, `crm_agent/api/agent.py`

## UX Polish (November 2025) ✅

8. **Optimized RAG Answer Length** - Better readability
   - Issue: Answers could be too long or verbose
   - Fix: Target ~150 words, add truncation helper, optimize LLM prompt
   - File: `crm_agent/agent/tools_rag.py`
   - Impact: Faster reading, better mobile UX

9. **Normalized Similarity Scores** - User-friendly metrics
   - Issue: Raw cosine distances (0-2) not intuitive
   - Fix: Convert to similarity scores (0-1) where 1 = perfect match
   - Formula: `similarity = 1.0 - (distance / 2.0)`
   - File: `crm_agent/agent/tools_rag.py`

10. **Enforced Project Attribution** - No missing metadata
    - Issue: Sources could show `null` for project
    - Fix: Require project name on upload, validate and normalize
    - Fallback: Shows "Unknown" instead of null
    - Files: `crm_agent/api/docs.py`, `crm_agent/agent/tools_rag.py`

## Next goals (planned)
1) ✅ Brochure upload + ingest to Chroma (RAG store) - **DONE**
2) ✅ Vanna T2SQL init + seed examples - **DONE**
3) ✅ **LangGraph router MVP** (RAG vs T2SQL) - **DONE**
   - ✅ Intent detection with confidence scoring
   - ✅ Clarify route for low-confidence queries
   - ✅ RAG summarization with LLM
   - ✅ Conversation memory with checkpointer
   - ✅ Proper metadata in sources
4) Campaign creation + personalized email generation - **NEXT**
5) Handle customer replies with AI agent
6) Metrics and dashboard endpoints


