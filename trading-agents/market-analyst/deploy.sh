#!/bin/bash

PROJECT_ID=$(gcloud config get-value project)
LOCATION=us-central1

gcloud run deploy market-analyst \
    --source . \
    --region $LOCATION \
    --allow-unauthenticated \
    --memory 1Gi \
    --cpu 1 \
    --service-account=trading-agents@${PROJECT_ID}.iam.gserviceaccount.com \
    --set-env-vars "PROJECT_ID=$PROJECT_ID,LOCATION=$LOCATION"
