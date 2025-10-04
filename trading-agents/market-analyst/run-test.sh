#!/bin/bash

PROJECT_ID=$(gcloud config get-value project)
LOCATION=us-central1

MARKET_ANALYST_URL=$(gcloud run services describe market-analyst --region us-central1 --format 'value(status.url)')

echo ""
curl $MARKET_ANALYST_URL/
echo ""

echo ""
curl $MARKET_ANALYST_URL/health
echo ""

echo ""
curl $MARKET_ANALYST_URL/market-summary
echo ""

echo ""
curl -X POST $MARKET_ANALYST_URL/analyze -H "Content-Type: application/json" -d '{"symbol": "AAPL", "analysis_type": "technical", "session_id": "test-aapl-001"}'
echo ""

echo ""
curl -X POST $MARKET_ANALYST_URL/analyze -H "Content-Type: application/json" -d '{"symbol": "TSLA", "analysis_type": "technical", "session_id": "test-tsla-001"}'
echo ""

echo ""
curl -X POST $MARKET_ANALYST_URL/analyze -H "Content-Type: application/json" -d '{"symbol": "GOOGL", "analysis_type": "technical", "session_id": "test-googl-001"}'
echo ""

echo ""
curl -X POST $MARKET_ANALYST_URL/analyze -H "Content-Type: application/json" -d '{"symbol": "MSFT", "analysis_type": "technical", "session_id": "test-msft-001"}'
echo ""
