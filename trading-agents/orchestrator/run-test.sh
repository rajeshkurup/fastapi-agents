#!/bin/bash

PROJECT_ID=$(gcloud config get-value project)
LOCATION=us-central1

TRADING_ORCHESTRATOR_URL=$(gcloud run services describe trading-orchestrator --region us-central1 --format 'value(status.url)')

echo ""
curl $TRADING_ORCHESTRATOR_URL/
echo ""

echo ""
curl $TRADING_ORCHESTRATOR_URL/health
echo ""

echo ""
curl -X POST $TRADING_ORCHESTRATOR_URL/trading-workflow -H "Content-Type: application/json" -d '{"symbol": "AAPL", "quantity": 50, "user_id": "test_user", "auto-execute": true}'
echo ""

echo ""
curl -X POST $TRADING_ORCHESTRATOR_URL/natural-language-trading -H "Content-Type: application/json" -d '{"query": "Should I buy 100 shares of Apple stock?", "user_id": "test_user"}'
echo ""

echo ""
curl $TRADING_ORCHESTRATOR_URL/users/test_user/sessions
echo ""

echo ""
curl $TRADING_ORCHESTRATOR_URL/users/test_user/trades
echo ""

echo ""
curl $TRADING_ORCHESTRATOR_URL/sessions/session-test_user-AAPL-1759535229
echo ""
