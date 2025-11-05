# Quick Start Guide - CRM Agent

Get up and running with the CRM Agent in 5 minutes.

---

## 1. Install & Setup (2 minutes)

```bash
# Navigate to project
cd /home/hafdaoui/Documents/Proplens/crm_agent

# Activate virtual environment
source ../.venv/bin/activate

# Install dependencies (if not already done)
pip install -r requirements.txt
```

---

## 2. Start the Server (30 seconds)

```bash
cd app
python manage.py runserver
```

**Server URL:** http://127.0.0.1:8000

---

## 3. Access Swagger Docs (30 seconds)

Open in browser: http://127.0.0.1:8000/api/docs

You'll see interactive API documentation with "Try it out" functionality.

---

## 4. Test with cURL (2 minutes)

### Get JWT Token

```bash
BASE="http://127.0.0.1:8000"

# Login
TOKEN=$(curl -s -X POST "$BASE/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin"}' | jq -r '.access')

echo "Your token: $TOKEN"
```

### Test Agent (Property Question)

```bash
curl -X POST "$BASE/api/agent/query" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question": "What amenities does Beachgate have?"}' | jq
```

### Test Agent (Analytics)

```bash
curl -X POST "$BASE/api/agent/query" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question": "How many Connected leads do we have?"}' | jq
```

### Create Test Campaign

```bash
curl -X POST "$BASE/api/campaigns" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Quick Test Campaign",
    "project": "Beachgate by Address",
    "channel": "email",
    "offer_text": "5% discount",
    "lead_ids": [1, 2, 3]
  }' | jq
```

---

## 5. Run Tests (1 minute)

```bash
cd /home/hafdaoui/Documents/Proplens/crm_agent
source ../.venv/bin/activate
python run_tests.py
```

**Expected:** All tests pass, DeepEval scores generated.

---

## Key Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/health` | GET | Health check |
| `/api/auth/login` | POST | Get JWT token |
| `/api/agent/query` | POST | **Main feature** - AI agent routing |
| `/api/campaigns` | POST | Create campaign with AI emails |
| `/api/campaigns/{id}/metrics` | GET | Campaign performance |
| `/api/leads/shortlist` | POST | Filter leads (2+ filters) |
| `/api/docs/search` | GET | Search property brochures |
| `/api/t2sql/query` | POST | Natural language SQL |

---

## Swagger Quick Actions

1. **Authenticate:**
   - Click "Authorize" button
   - Login via `/api/auth/login` to get token
   - Enter token: `Bearer <your-token>`

2. **Test Agent:**
   - Expand `/api/agent/query`
   - Click "Try it out"
   - Enter question: "What amenities does Beachgate have?"
   - Click "Execute"

3. **Create Campaign:**
   - Expand `/api/campaigns`
   - Click "Try it out"
   - Use example payload
   - Click "Execute"

---

## Architecture Overview

```
User Query → Agent Router (LangGraph)
              ├─→ RAG Tool (ChromaDB + Groq)
              ├─→ T2SQL Tool (Vanna + Groq)
              └─→ Clarify (Direct response)
```

---

## Common Test Scenarios

### 1. Property Q&A
```bash
curl -X POST "$BASE/api/agent/query" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question": "What are the unit types at Beachgate?"}' | jq
```

### 2. Analytics
```bash
curl -X POST "$BASE/api/agent/query" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question": "Count leads by project"}' | jq
```

### 3. Campaign + Follow-up
```bash
# Create campaign
CAMPAIGN_ID=$(curl -s -X POST "$BASE/api/campaigns" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Test","project":"Beachgate by Address","channel":"email","offer_text":"5%","lead_ids":[1,2]}' \
  | jq -r '.campaign_id')

# Simulate reply
curl -X POST "$BASE/api/campaigns/$CAMPAIGN_ID/lead/1/reply" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "I want to schedule a visit"}' | jq

# Check followups
curl "$BASE/api/campaigns/$CAMPAIGN_ID/followups" \
  -H "Authorization: Bearer $TOKEN" | jq
```

---

## Files Overview

| File | Purpose |
|------|---------|
| `README.md` | **Full documentation** - Start here |
| `RUNBOOK.md` | Comprehensive test commands |
| `TESTING.md` | Detailed testing guide |
| `QUICK_START.md` | This file - Quick reference |
| `run_tests.py` | Automated test runner |
| `agent_evaluation_scores.json` | DeepEval results |

---

## Troubleshooting

### Port 8000 already in use
```bash
# Kill existing server
lsof -ti:8000 | xargs kill -9
# Restart
python manage.py runserver
```

### Token expired
```bash
# Get new token
TOKEN=$(curl -s -X POST "$BASE/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin"}' | jq -r '.access')
```

### No ChromaDB results
```bash
# Check document count
curl "$BASE/api/docs/count" -H "Authorization: Bearer $TOKEN" | jq
# Should show total_chunks > 0
```

---

## What's Next?

- **Full docs:** Read [README.md](README.md)
- **All tests:** See [RUNBOOK.md](RUNBOOK.md)
- **Deploy:** Follow deployment guide (coming soon)

---

## Support

For detailed documentation on any feature:
1. Check [README.md](README.md) - Comprehensive guide
2. Check [TESTING.md](TESTING.md) - Testing scenarios
3. Use Swagger docs - http://127.0.0.1:8000/api/docs
4. Check RUNBOOK.md - All cURL commands

**Happy Testing!** 🚀
