#!/bin/bash

PROJECT_ID=$(gcloud config get-value project)
LOCATION=us-central1

STOCK_TRADER_URL=$(gcloud run services describe stock-trader --region us-central1 --format 'value(status.url)')

echo ""
curl $STOCK_TRADER_URL/
echo ""

echo ""
curl $STOCK_TRADER_URL/health
echo ""

echo ""
curl -X POST $STOCK_TRADER_URL/execute-trade -H "Content-Type: application/json" -d '{"symbol": "AAPL", "action": "BUY", "quantity": 100, "price": 150.00, "session_id": "test-002"}'
echo ""

echo ""
curl -X POST $STOCK_TRADER_URL/execute-trade -H "Content-Type: application/json" -d '{"symbol": "TSLA", "action": "SELL", "quantity": 100, "price": 150.00, "session_id": "test-002"}'
echo ""

echo ""
curl -X POST $STOCK_TRADER_URL/execute-trade -H "Content-Type: application/json" -d '{"symbol": "GOOGL", "action": "HOLD", "quantity": 100, "price": 150.00, "session_id": "test-002"}'
echo ""

echo ""
curl -X POST $STOCK_TRADER_URL/execute-trade -H "Content-Type: application/json" -d '{"symbol": "MSFT", "action": "BUY", "quantity": 100, "price": 150.00, "session_id": "test-002"}'
echo ""
