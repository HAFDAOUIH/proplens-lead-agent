#!/bin/bash
# Quick API Test - CRM Agent Production

BASE="https://proplens-lead-agent-production.up.railway.app"

echo "🔍 Testing CRM Agent API at: $BASE"
echo ""

echo "1️⃣ Health Check:"
curl -s "$BASE/api/health" | jq
echo ""

echo "2️⃣ Login (create superuser first if this fails):"
LOGIN=$(curl -s -X POST "$BASE/api/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin"}')
echo "$LOGIN" | jq
TOKEN=$(echo "$LOGIN" | jq -r '.access')
echo ""

if [ "$TOKEN" != "null" ] && [ ! -z "$TOKEN" ]; then
    H="Authorization: Bearer $TOKEN"
    CT="Content-Type: application/json"

    echo "3️⃣ T2SQL Query - Count leads:"
    curl -s -X POST "$BASE/api/agent/query" \
      -H "$H" -H "$CT" \
      -d '{"question": "How many leads do we have?"}' | jq
    echo ""

    echo "4️⃣ RAG Query - Property info:"
    curl -s -X POST "$BASE/api/agent/query" \
      -H "$H" -H "$CT" \
      -d '{"question": "What amenities does Beachgate have?"}' | jq
    echo ""

    echo "✅ Tests complete!"
else
    echo "❌ Login failed. Create a superuser first:"
    echo "   1. Install Railway CLI: npm i -g @railway/cli"
    echo "   2. Login: railway login"
    echo "   3. Link project: railway link"
    echo "   4. Create superuser: railway run python manage.py createsuperuser"
fi
