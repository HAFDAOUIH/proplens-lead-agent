# 🚀 CRM Agent Production API - Testing Guide

**Live URL:** `https://proplens-lead-agent-production.up.railway.app`

## 📋 Table of Contents

1. [Quick Start](#quick-start)
2. [Create Superuser](#create-superuser)
3. [API Endpoints](#api-endpoints)
4. [Test Scripts](#test-scripts)
5. [Example Requests](#example-requests)

---

## Quick Start

### Run Quick Test
```bash
./quick_test.sh
```

### Run Full Test Suite
```bash
./test_production.sh
```

---

## Create Superuser

Before you can login, you need to create a Django superuser:

### Method 1: Railway CLI
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Link to your project
railway link

# Create superuser
railway run python /crm_agent/app/manage.py createsuperuser
```

### Method 2: Railway Dashboard
1. Go to your Railway project
2. Click on your service
3. Go to "Settings" → "Shells"
4. Run: `cd /crm_agent/app && python manage.py createsuperuser`

---

## API Endpoints

### 🟢 Public Endpoints (No Auth Required)

#### Health Check
```bash
curl https://proplens-lead-agent-production.up.railway.app/api/health
```

**Response:**
```json
{"status": "ok"}
```

#### API Documentation
```
https://proplens-lead-agent-production.up.railway.app/api/docs
```

#### OpenAPI Schema
```bash
curl https://proplens-lead-agent-production.up.railway.app/api/openapi.json
```

---

### 🔐 Authentication

#### Login
```bash
curl -X POST https://proplens-lead-agent-production.up.railway.app/api/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin"
  }'
```

**Response:**
```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Use the token in subsequent requests:**
```bash
TOKEN="<your-token-here>"
curl -H "Authorization: Bearer $TOKEN" <endpoint>
```

---

### 👥 Lead Management

#### List All Leads
```bash
curl -H "Authorization: Bearer $TOKEN" \
  https://proplens-lead-agent-production.up.railway.app/api/leads
```

#### Get Lead by ID
```bash
curl -H "Authorization: Bearer $TOKEN" \
  https://proplens-lead-agent-production.up.railway.app/api/leads/1
```

#### Create New Lead
```bash
curl -X POST https://proplens-lead-agent-production.up.railway.app/api/leads \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "+971501234567",
    "project_enquired": "Beachgate",
    "unit_type": "2BR",
    "budget_min": 500000,
    "budget_max": 750000
  }'
```

#### Update Lead
```bash
curl -X PUT https://proplens-lead-agent-production.up.railway.app/api/leads/1 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe Updated",
    "email": "john@example.com",
    "phone": "+971501234567",
    "project_enquired": "Beachgate",
    "unit_type": "3BR",
    "budget_min": 600000,
    "budget_max": 800000
  }'
```

#### Delete Lead
```bash
curl -X DELETE https://proplens-lead-agent-production.up.railway.app/api/leads/1 \
  -H "Authorization: Bearer $TOKEN"
```

---

### 🤖 AI Agent Queries

The agent automatically routes queries to the right subsystem:
- **T2SQL**: Database queries (counts, filters, aggregations)
- **RAG**: Semantic search over documents (amenities, features, location)

#### T2SQL Examples

**Count all leads:**
```bash
curl -X POST https://proplens-lead-agent-production.up.railway.app/api/agent/query \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question": "How many leads do we have?"}'
```

**Connected leads:**
```bash
curl -X POST https://proplens-lead-agent-production.up.railway.app/api/agent/query \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question": "Show me all Connected leads"}'
```

**Leads by status:**
```bash
curl -X POST https://proplens-lead-agent-production.up.railway.app/api/agent/query \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question": "Count leads by status"}'
```

**High-budget leads:**
```bash
curl -X POST https://proplens-lead-agent-production.up.railway.app/api/agent/query \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question": "Show leads with budget over 1 million"}'
```

**Leads by project:**
```bash
curl -X POST https://proplens-lead-agent-production.up.railway.app/api/agent/query \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question": "How many leads are interested in Beachgate?"}'
```

#### RAG Examples

**Property amenities:**
```bash
curl -X POST https://proplens-lead-agent-production.up.railway.app/api/agent/query \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question": "What amenities does Beachgate have?"}'
```

**Location info:**
```bash
curl -X POST https://proplens-lead-agent-production.up.railway.app/api/agent/query \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question": "Tell me about the location"}'
```

**Unit types:**
```bash
curl -X POST https://proplens-lead-agent-production.up.railway.app/api/agent/query \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question": "What unit types are available?"}'
```

---

### 📧 Campaign Management

#### List Campaigns
```bash
curl -H "Authorization: Bearer $TOKEN" \
  https://proplens-lead-agent-production.up.railway.app/api/campaigns
```

#### Create Campaign
```bash
curl -X POST https://proplens-lead-agent-production.up.railway.app/api/campaigns \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Beachgate Launch",
    "description": "Promotional campaign for Beachgate",
    "target_segment": "high_budget"
  }'
```

---

### 📄 Document Ingestion

#### List Documents
```bash
curl -H "Authorization: Bearer $TOKEN" \
  https://proplens-lead-agent-production.up.railway.app/api/docs
```

#### Upload Document
```bash
curl -X POST https://proplens-lead-agent-production.up.railway.app/api/docs/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/path/to/brochure.pdf"
```

---

## Test Scripts

### Quick Test (`quick_test.sh`)
Fast 30-second test of core functionality:
- Health check
- Login
- One T2SQL query
- One RAG query

```bash
./quick_test.sh
```

### Full Test Suite (`test_production.sh`)
Comprehensive test covering:
- All public endpoints
- Authentication
- CRUD operations on leads
- Multiple T2SQL queries
- Multiple RAG queries
- Campaign management
- Document management

```bash
./test_production.sh
```

---

## Common Issues

### Issue: Login returns 401
**Solution:** Create a superuser first (see [Create Superuser](#create-superuser))

### Issue: Agent returns empty results
**Solution:** Ingest documents first using the `/api/docs/upload` endpoint

### Issue: T2SQL returns no data
**Solution:** Create some test leads using `/api/leads` POST endpoint

---

## Next Steps

1. ✅ Create superuser
2. ✅ Run `./quick_test.sh` to verify basic functionality
3. ✅ Create test leads via API
4. ✅ Upload property brochures
5. ✅ Test AI agent with various queries
6. ✅ Run full test suite: `./test_production.sh`

---

## Production URL

**Base URL:** `https://proplens-lead-agent-production.up.railway.app`

**API Docs:** `https://proplens-lead-agent-production.up.railway.app/api/docs`

**Health Check:** `https://proplens-lead-agent-production.up.railway.app/api/health`

---

## Support

For issues or questions, check the deployment logs in Railway dashboard.
