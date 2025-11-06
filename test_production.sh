#!/bin/bash

# CRM Agent Production API Test Suite
# URL: https://proplens-lead-agent-production.up.railway.app

BASE="https://proplens-lead-agent-production.up.railway.app"

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║     CRM Agent Production API Test Suite                       ║"
echo "╔════════════════════════════════════════════════════════════════╗"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
PASSED=0
FAILED=0

test_endpoint() {
    local name="$1"
    local command="$2"
    echo -e "${YELLOW}Testing: $name${NC}"
    if eval "$command"; then
        echo -e "${GREEN}✓ PASSED${NC}\n"
        ((PASSED++))
    else
        echo -e "${RED}✗ FAILED${NC}\n"
        ((FAILED++))
    fi
}

echo "════════════════════════════════════════════════════════════════"
echo "1. PUBLIC ENDPOINTS (No Authentication Required)"
echo "════════════════════════════════════════════════════════════════"
echo ""

test_endpoint "Health Check" \
    "curl -s $BASE/api/health | jq -e '.status == \"ok\"' > /dev/null"

test_endpoint "API Documentation" \
    "curl -s $BASE/api/docs | grep -q 'CRM Agent API'"

test_endpoint "OpenAPI Schema" \
    "curl -s $BASE/api/openapi.json | jq -e '.openapi' > /dev/null"

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "2. AUTHENTICATION"
echo "════════════════════════════════════════════════════════════════"
echo ""

echo -e "${YELLOW}Testing: Login with default credentials${NC}"
LOGIN_RESPONSE=$(curl -s -X POST "$BASE/api/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}')

echo "$LOGIN_RESPONSE" | jq '.'

# Check if login succeeded
if echo "$LOGIN_RESPONSE" | jq -e '.access' > /dev/null 2>&1; then
    TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.access')
    echo -e "${GREEN}✓ Login successful${NC}"
    echo "Token (first 50 chars): ${TOKEN:0:50}..."
    ((PASSED++))
else
    echo -e "${RED}✗ Login failed${NC}"
    echo "Note: You need to create a superuser first:"
    echo "  Railway CLI: railway run python manage.py createsuperuser"
    ((FAILED++))
    TOKEN=""
fi
echo ""

if [ -z "$TOKEN" ]; then
    echo -e "${RED}⚠ Skipping authenticated tests (no token)${NC}"
    echo ""
else
    H="Authorization: Bearer $TOKEN"
    CT="Content-Type: application/json"

    echo "════════════════════════════════════════════════════════════════"
    echo "3. LEAD MANAGEMENT"
    echo "════════════════════════════════════════════════════════════════"
    echo ""

    test_endpoint "List all leads" \
        "curl -s -H '$H' $BASE/api/leads | jq -e 'type == \"array\"' > /dev/null"

    echo -e "${YELLOW}Testing: Create new lead${NC}"
    NEW_LEAD=$(curl -s -X POST "$BASE/api/leads" \
      -H "$H" -H "$CT" \
      -d '{
        "name": "Test Lead",
        "email": "test@example.com",
        "phone": "+1234567890",
        "project_enquired": "Beachgate",
        "unit_type": "2BR",
        "budget_min": 500000,
        "budget_max": 750000
      }')
    echo "$NEW_LEAD" | jq '.'

    if echo "$NEW_LEAD" | jq -e '.id' > /dev/null 2>&1; then
        LEAD_ID=$(echo "$NEW_LEAD" | jq -r '.id')
        echo -e "${GREEN}✓ Lead created with ID: $LEAD_ID${NC}"
        ((PASSED++))
    else
        echo -e "${RED}✗ Failed to create lead${NC}"
        ((FAILED++))
    fi
    echo ""

    if [ ! -z "$LEAD_ID" ]; then
        test_endpoint "Get lead by ID" \
            "curl -s -H '$H' $BASE/api/leads/$LEAD_ID | jq -e '.id == $LEAD_ID' > /dev/null"

        echo -e "${YELLOW}Testing: Update lead${NC}"
        UPDATE_RESPONSE=$(curl -s -X PUT "$BASE/api/leads/$LEAD_ID" \
          -H "$H" -H "$CT" \
          -d '{
            "name": "Updated Test Lead",
            "email": "updated@example.com",
            "phone": "+1234567890",
            "project_enquired": "Beachgate",
            "unit_type": "3BR",
            "budget_min": 600000,
            "budget_max": 800000
          }')
        echo "$UPDATE_RESPONSE" | jq '.'

        if echo "$UPDATE_RESPONSE" | jq -e '.name == "Updated Test Lead"' > /dev/null 2>&1; then
            echo -e "${GREEN}✓ Lead updated successfully${NC}"
            ((PASSED++))
        else
            echo -e "${RED}✗ Failed to update lead${NC}"
            ((FAILED++))
        fi
        echo ""

        test_endpoint "Delete lead" \
            "curl -s -X DELETE -H '$H' $BASE/api/leads/$LEAD_ID | jq -e '.success == true' > /dev/null"
    fi

    echo ""
    echo "════════════════════════════════════════════════════════════════"
    echo "4. AI AGENT - TEXT-TO-SQL (T2SQL)"
    echo "════════════════════════════════════════════════════════════════"
    echo ""

    echo -e "${YELLOW}Query: How many leads do we have?${NC}"
    curl -s -X POST "$BASE/api/agent/query" \
      -H "$H" -H "$CT" \
      -d '{"question": "How many leads do we have?"}' | jq '.'
    echo ""

    echo -e "${YELLOW}Query: Show me all Connected leads${NC}"
    curl -s -X POST "$BASE/api/agent/query" \
      -H "$H" -H "$CT" \
      -d '{"question": "Show me all Connected leads"}' | jq '.'
    echo ""

    echo -e "${YELLOW}Query: Count leads by status${NC}"
    curl -s -X POST "$BASE/api/agent/query" \
      -H "$H" -H "$CT" \
      -d '{"question": "Count leads by status"}' | jq '.'
    echo ""

    echo -e "${YELLOW}Query: Leads with budget over 500k${NC}"
    curl -s -X POST "$BASE/api/agent/query" \
      -H "$H" -H "$CT" \
      -d '{"question": "Show leads with budget over 500000"}' | jq '.'
    echo ""

    echo ""
    echo "════════════════════════════════════════════════════════════════"
    echo "5. AI AGENT - RAG (Retrieval-Augmented Generation)"
    echo "════════════════════════════════════════════════════════════════"
    echo ""

    echo -e "${YELLOW}Query: What amenities does Beachgate have?${NC}"
    curl -s -X POST "$BASE/api/agent/query" \
      -H "$H" -H "$CT" \
      -d '{"question": "What amenities does Beachgate have?"}' | jq '.'
    echo ""

    echo -e "${YELLOW}Query: Tell me about the location of the project${NC}"
    curl -s -X POST "$BASE/api/agent/query" \
      -H "$H" -H "$CT" \
      -d '{"question": "Tell me about the location of the project"}' | jq '.'
    echo ""

    echo ""
    echo "════════════════════════════════════════════════════════════════"
    echo "6. CAMPAIGN MANAGEMENT"
    echo "════════════════════════════════════════════════════════════════"
    echo ""

    test_endpoint "List campaigns" \
        "curl -s -H '$H' $BASE/api/campaigns | jq -e 'type == \"array\"' > /dev/null"

    echo -e "${YELLOW}Testing: Create campaign${NC}"
    CAMPAIGN=$(curl -s -X POST "$BASE/api/campaigns" \
      -H "$H" -H "$CT" \
      -d '{
        "name": "Test Campaign",
        "description": "Testing campaign creation",
        "target_segment": "all"
      }')
    echo "$CAMPAIGN" | jq '.'

    if echo "$CAMPAIGN" | jq -e '.id' > /dev/null 2>&1; then
        CAMPAIGN_ID=$(echo "$CAMPAIGN" | jq -r '.id')
        echo -e "${GREEN}✓ Campaign created with ID: $CAMPAIGN_ID${NC}"
        ((PASSED++))
    else
        echo -e "${RED}✗ Failed to create campaign${NC}"
        ((FAILED++))
    fi
    echo ""

    echo ""
    echo "════════════════════════════════════════════════════════════════"
    echo "7. DOCUMENT INGESTION"
    echo "════════════════════════════════════════════════════════════════"
    echo ""

    test_endpoint "List ingested documents" \
        "curl -s -H '$H' $BASE/api/docs | jq -e 'type == \"array\"' > /dev/null"

fi

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "TEST SUMMARY"
echo "════════════════════════════════════════════════════════════════"
TOTAL=$((PASSED + FAILED))
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"
echo "Total:  $TOTAL"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 All tests passed!${NC}"
    exit 0
else
    echo -e "${YELLOW}⚠ Some tests failed. Review the output above.${NC}"
    exit 1
fi
