# Testing Guide - CRM Agent

Complete guide for testing the CRM Agent system manually and automatically.

---

## Quick Start Testing

### 1. Start the Server

```bash
cd /home/hafdaoui/Documents/Proplens/crm_agent/app
source ../../.venv/bin/activate
python manage.py runserver
```

Server will start at: http://127.0.0.1:8000

---

## Automated Testing

### Run All Tests

```bash
cd /home/hafdaoui/Documents/Proplens/crm_agent
source ../.venv/bin/activate
python run_tests.py
```

**Expected Output:**
```
============================================================
CRM Agent Test Runner
============================================================

=== Running API Tests ===

✓ Health endpoint
✓ User login
✓ Document count
✓ Document search
✓ Agent RAG routing

=== Test Summary ===
Total: 5
Passed: 5
Failed: 0

=== Running DeepEval Evaluation ===

Test case 1: What amenities are available at Beachgate by Address?
  ✓ Answer generated (4 sources)
  ✓ Faithfulness: 1.00
  ✓ Relevancy: 0.80

✓ Evaluation scores saved to: agent_evaluation_scores.json

=== DeepEval Summary ===
Average Faithfulness: 1.00
Average Relevancy: 0.80
Successful: 3/3

============================================================
✓ All tests and evaluations completed successfully!
```

### Run Pytest Tests

```bash
cd /home/hafdaoui/Documents/Proplens/crm_agent/app
source ../../.venv/bin/activate
PYTHONPATH=/home/hafdaoui/Documents/Proplens/crm_agent:$PYTHONPATH pytest tests/ -v
```

---

## Manual API Testing

### Setup

```bash
# Set base URL
BASE="http://127.0.0.1:8000"

# Get JWT token
TOKEN=$(curl -s -X POST "$BASE/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin"}' | jq -r '.access')

echo "Token: $TOKEN"
```

---

### Test 1: Health Check

```bash
curl -s "$BASE/api/health" | jq
```

**Expected Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-11-05T16:30:00Z"
}
```

---

### Test 2: Authentication

```bash
curl -s -X POST "$BASE/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin"}' | jq
```

**Expected Response:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

---

### Test 3: Agent Query - RAG Route

```bash
curl -s -X POST "$BASE/api/agent/query" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question": "What amenities does Beachgate by Address have?"}' | jq
```

**Expected Response:**
```json
{
  "route": "rag",
  "answer": "At Beachgate By Address, available amenities include:\n* Swimming Pool & Kids' Pool\n* Multi-Function Room\n* Fully Equipped Gym...",
  "sources": [
    {
      "text": "Beachgate features...",
      "metadata": {"page": 3, "project": "Beachgate by Address"}
    }
  ],
  "confidence": 0.95,
  "thread_id": "abc-123"
}
```

---

### Test 4: Agent Query - T2SQL Route

```bash
curl -s -X POST "$BASE/api/agent/query" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question": "How many Connected leads do we have?"}' | jq
```

**Expected Response:**
```json
{
  "route": "t2sql",
  "sql": "SELECT COUNT(*) FROM coreapp_lead WHERE status = 'Connected'",
  "rows": [[45]],
  "columns": ["count"],
  "summary": "There are 45 Connected leads",
  "confidence": 0.9,
  "thread_id": "def-456"
}
```

---

### Test 5: Document Search

```bash
curl -s "$BASE/api/docs/search?q=amenities&k=4" \
  -H "Authorization: Bearer $TOKEN" | jq
```

**Expected Response:**
```json
{
  "matches": [
    {
      "text": "Beachgate features swimming pool...",
      "metadata": {"page": 3, "project": "Beachgate by Address"},
      "similarity": 0.89
    }
  ]
}
```

---

### Test 6: Lead Shortlisting

```bash
curl -s -X POST "$BASE/api/leads/shortlist" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "project_enquired": "Beachgate by Address",
    "status": "Connected",
    "budget_min": 1000000,
    "budget_max": 3000000
  }' | jq
```

**Expected Response:**
```json
{
  "count": 15,
  "leads": [
    {
      "id": 1,
      "name": "John Doe",
      "email": "john@example.com",
      "phone": "+971501234567",
      "unit_type": "2 bed",
      "budget_min": 1500000,
      "budget_max": 2000000,
      "status": "Connected"
    }
  ]
}
```

---

### Test 7: Create Campaign

```bash
curl -s -X POST "$BASE/api/campaigns" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Campaign",
    "project": "Beachgate by Address",
    "channel": "email",
    "offer_text": "5% discount on select units",
    "lead_ids": [1, 2, 3]
  }' | jq
```

**Expected Response:**
```json
{
  "campaign_id": 1,
  "campaign_name": "Test Campaign",
  "sent_count": 3,
  "sample_messages": [
    {
      "lead_id": 1,
      "lead_name": "John Doe",
      "subject": "Exclusive: Beachgate 2BR with Private Beach Access",
      "body": "Dear John, Based on your interest in 2-bedroom units..."
    }
  ]
}
```

---

### Test 8: Campaign Metrics

```bash
curl -s "$BASE/api/campaigns/1/metrics" \
  -H "Authorization: Bearer $TOKEN" | jq
```

**Expected Response:**
```json
{
  "campaign_id": 1,
  "campaign_name": "Test Campaign",
  "leads_shortlisted": 3,
  "messages_sent": 3,
  "unique_leads_responded": 0,
  "goals_achieved_count": 0
}
```

---

### Test 9: Lead Reply

```bash
curl -s -X POST "$BASE/api/campaigns/1/lead/1/reply" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "What are the payment plans available?"}' | jq
```

**Expected Response:**
```json
{
  "thread_id": 1,
  "lead_message": "What are the payment plans available?",
  "agent_response": "For Beachgate by Address, typical payment plans...",
  "created_at": "2025-11-05T16:00:00Z"
}
```

---

### Test 10: Campaign Followups

```bash
curl -s "$BASE/api/campaigns/1/followups" \
  -H "Authorization: Bearer $TOKEN" | jq
```

**Expected Response:**
```json
{
  "campaign_id": 1,
  "total_threads": 1,
  "followups": [
    {
      "thread_id": 1,
      "lead_name": "John Doe",
      "message_count": 2,
      "last_updated": "2025-11-05T16:00:00Z",
      "recent_messages": [
        {
          "role": "lead",
          "content": "What are the payment plans available?",
          "created_at": "2025-11-05T15:59:00Z"
        },
        {
          "role": "agent",
          "content": "For Beachgate by Address...",
          "created_at": "2025-11-05T16:00:00Z"
        }
      ]
    }
  ]
}
```

---

## Interactive Testing with Swagger

The easiest way to test the API is using the built-in Swagger documentation:

1. **Start the server:**
   ```bash
   cd app && python manage.py runserver
   ```

2. **Open Swagger UI:**
   ```
   http://127.0.0.1:8000/api/docs
   ```

3. **Authenticate:**
   - Click "Authorize" button
   - Login to get token: POST `/api/auth/login`
   - Copy the `access` token
   - Enter in Authorize dialog: `Bearer <token>`
   - Click "Authorize"

4. **Test endpoints:**
   - All endpoints are now available in "Try it out" mode
   - Fill in request bodies
   - Click "Execute"
   - View responses

---

## Testing Scenarios

### Scenario 1: Lead Nurturing Workflow

```bash
# 1. Shortlist leads
LEAD_IDS=$(curl -s -X POST "$BASE/api/leads/shortlist" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"project_enquired": "Beachgate by Address", "status": "Connected"}' \
  | jq -r '.leads[0:3] | map(.id) | @json')

echo "Selected leads: $LEAD_IDS"

# 2. Create campaign
CAMPAIGN_ID=$(curl -s -X POST "$BASE/api/campaigns" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"name\": \"Test Campaign\", \"project\": \"Beachgate by Address\", \"channel\": \"email\", \"offer_text\": \"5% discount\", \"lead_ids\": $LEAD_IDS}" \
  | jq -r '.campaign_id')

echo "Created campaign: $CAMPAIGN_ID"

# 3. Check metrics
curl -s "$BASE/api/campaigns/$CAMPAIGN_ID/metrics" \
  -H "Authorization: Bearer $TOKEN" | jq

# 4. Simulate lead reply
curl -s -X POST "$BASE/api/campaigns/$CAMPAIGN_ID/lead/1/reply" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "I am interested in a site visit"}' | jq

# 5. Check followups
curl -s "$BASE/api/campaigns/$CAMPAIGN_ID/followups" \
  -H "Authorization: Bearer $TOKEN" | jq
```

---

### Scenario 2: Property Q&A with Follow-ups

```bash
# 1. Ask initial question
THREAD_ID=$(curl -s -X POST "$BASE/api/agent/query" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question": "What properties are available?"}' \
  | jq -r '.thread_id')

echo "Thread ID: $THREAD_ID"

# 2. Ask follow-up question
curl -s -X POST "$BASE/api/agent/query" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"question\": \"Tell me more about Beachgate\", \"thread_id\": \"$THREAD_ID\"}" | jq

# 3. Ask specific follow-up
curl -s -X POST "$BASE/api/agent/query" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"question\": \"What are the prices?\", \"thread_id\": \"$THREAD_ID\"}" | jq
```

---

### Scenario 3: Analytics Queries

```bash
# Count queries
curl -s -X POST "$BASE/api/agent/query" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question": "How many leads are there?"}' | jq

# Aggregation queries
curl -s -X POST "$BASE/api/agent/query" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question": "Show me leads grouped by status"}' | jq

# Filter queries
curl -s -X POST "$BASE/api/agent/query" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question": "List all Connected leads"}' | jq
```

---

## Performance Testing

### Test Response Times

```bash
# RAG query performance
time curl -s -X POST "$BASE/api/agent/query" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question": "What amenities does Beachgate have?"}' > /dev/null

# T2SQL query performance
time curl -s -X POST "$BASE/api/agent/query" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question": "How many leads are there?"}' > /dev/null

# Campaign creation performance (3 leads)
time curl -s -X POST "$BASE/api/campaigns" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Perf Test", "project": "Beachgate by Address", "channel": "email", "offer_text": "test", "lead_ids": [1,2,3]}' > /dev/null
```

**Expected Response Times:**
- RAG query: 1-3 seconds
- T2SQL query: 2-4 seconds
- Campaign creation (3 leads): 5-10 seconds

---

## Evaluation Testing

### Run DeepEval

```bash
python run_tests.py
```

Checks `agent_evaluation_scores.json` for:
- **Faithfulness**: ≥ 0.7 (answers grounded in sources)
- **Relevancy**: ≥ 0.7 (answers address questions)

---

## Troubleshooting

### Issue: 401 Unauthorized

**Solution:** Token expired or invalid
```bash
# Get new token
TOKEN=$(curl -s -X POST "$BASE/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin"}' | jq -r '.access')
```

### Issue: No results from RAG

**Solution:** Check ChromaDB has documents
```bash
curl -s "$BASE/api/docs/count" -H "Authorization: Bearer $TOKEN" | jq
# Should show total_chunks > 0
```

### Issue: T2SQL errors

**Solution:** Reseed Vanna training
```bash
python manage.py shell
>>> from crm_agent.ingestion.vanna_seed import VannaSeeder
>>> VannaSeeder().seed()
```

---

## Full Test Script

Complete test script available in `RUNBOOK.md` with all cURL commands.

For comprehensive testing with all endpoints, see the [README.md](README.md) API Documentation section.
