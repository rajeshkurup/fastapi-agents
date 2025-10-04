#!/bin/bash

PROJECT_ID=$(gcloud config get-value project)
LOCATION=us-central1

MARKET_ANALYST_URL=$(gcloud run services describe market-analyst --region $LOCATION --format 'value(status.url)')
STOCK_TRADER_URL=$(gcloud run services describe stock-trader --region $LOCATION --format 'value(status.url)')

gcloud run deploy trading-orchestrator \
    --source . \
    --region $LOCATION \
    --allow-unauthenticated \
    --memory 1Gi \
    --cpu 1 \
    --service-account=trading-agents@${PROJECT_ID}.iam.gserviceaccount.com \
    --set-env-vars "PROJECT_ID=$PROJECT_ID,LOCATION=$LOCATION,MARKET_ANALYST_URL=$MARKET_ANALYST_URL,STOCK_TRADER_URL=$STOCK_TRADER_URL"
