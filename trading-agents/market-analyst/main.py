#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Market Analyst AI Agent.
"""

from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
import os
from datetime import datetime
from google.cloud import aiplatform
import vertexai
from vertexai.preview.generative_models import GenerativeModel
import json

app = FastAPI()

# Init Vertex AI
PROJECT_ID = os.getenv("PROJECT_ID", "")
LOCATION = os.getenv("LOCATION", "us-central1")

if PROJECT_ID:
    vertexai.init(project=PROJECT_ID, location=LOCATION)

class AnalysisRequest(BaseModel):
    symbol: str
    analysis_type: str
    session_id: str

class AnalysisResponse(BaseModel):
    symbol: str
    analysis: dict
    recommendation: str
    confidence: float
    timestamp: str
    llm_reasoning: str

@app.get("/")
def root():
    return {"message": "Market Analyst Service with LLM", "status": "running"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "agent": "market-analyst", "agent": "market-analyst"}

@app.post("/analyze")
def analyze_market(request: AnalysisRequest):
    """
    Analyzes market data and provides recommendations
    """

    if request.symbol == "AAPL":
        market_data = {
            "current_price": 150.00,
            "price_change": "+2.5%",
            "volume": "High",
            "52_week_high": 180.00,
            "52_week_low": 120.00,
            "pe_ratio": 28.5,
            "market_cap": "2.8T"
        }

    elif request.symbol == "GOOGL":
        market_data = {
            "current_price": 140.00,
            "price_change": "+0.3%",
            "volume": "Normal",
            "52_week_high": 155.00,
            "52_week_low": 110.00,
            "pe_ratio": 24.2,
            "market_cap": "1.7T"
        }

    elif request.symbol == "TSLA":
        market_data = {
            "current_price": 210.00,
            "price_change": "-3.2%",
            "volume": "High",
            "52_week_high": 300.00,
            "52_week_low": 150.00,
            "pe_ratio": 65.5,
            "market_cap": "650B"
        }

    else:
        market_data = {
            "current_price": 100.00,
            "price_change": "0.0%",
            "volume": "Normal",
            "52_week_high": 120.00,
            "52_week_low": 80.00,
            "pe_ratio": 20.0,
            "market_cap": "N/A"
        }

    # Use LLM to analyze the stock
    try:
        llm_analysis = analyze_with_llm(request.symbol, market_data, request.analysis_type)
    except Exception as e:
        print(f"LLM analysis failed: {e}")
        # Fallback to simple analysis
        llm_analysis = fallback_analysis(request.symbol, market_data)

    print(f"Analysis completed: {request.symbol} -> {llm_analysis['recommendation']}")

    return AnalysisResponse(
        symbol=request.symbol,
        analysis=llm_analysis["analysis"],
        recommendation=llm_analysis["recommendation"],
        confidence=llm_analysis["confidence"],
        timestamp=datetime.now().isoformat(),
        llm_reasoning=llm_analysis["reasoning"]
    )

def analyze_with_llm(symbol: str, market_data: dict, analysis_type: str) -> dict:
    """
    Use Gemini LLM to analyze stock data
    """
    prompt = f"""You are an expert market analyst. Analyze the following stock data and provide a recommendation.

    Stock Symbol: {symbol}
    Analysis Type: {analysis_type}

    Market Data:
    {json.dumps(market_data, indent=2)}

    Based on this data, provide:
    1. Technical analysis of price trends and volume
    2. A clear recommendation: BUY, SELL, or HOLD
    3. Confidence level (0.0 to 1.0)
    4. Key reasoning for your recommendation

    Format your response as JSON with this structure:
    {{
        "analysis": {{
            "price_trend": "bullish/bearish/neutral",
            "volume_analysis": "description",
            "technical_indicators": {{}},
            "key_factors": []
        }},
        "recommendation": "BUY/SELL/HOLD",
        "confidence": 0.85,
        "reasoning": "brief explanation"
    }}
    """

    # Init Gemini Model
    model = GenerativeModel("gemini-2.5-pro")

    response = model.generate_content(prompt)
    response_text = response.text

    # Extract JSON from response (handle markdown code blocks)
    if "```json" in response_text:
        json_str = response_text.split("```json")[1].split("```")[0].strip()
    elif "```" in response_text:
        json_str = response_text.split("```")[1].split("```")[0].strip()
    else:
        json_str = response_text.strip()
    
    result = json.loads(json_str)
    return result

def fallback_analysis(symbol: str, market_data: dict) -> dict:
    """
    Fallback analysis if LLM fails
    """
    price_change = float(market_data.get("price_change", "0%")).replace("%", "")

    if price_change > 2.0:
        recommendation = "BUY"
        confidence = 0.75
        reasoning = "Strong positive price movement"
    elif price_change < -2.0:
        recommendation = "SELL"
        confidence = 0.70
        reasoning = "Significant negative price movement"
    else:
        recommendation = "HOLD"
        confidence = 0.60
        reasoning = "Neutral market conditions"

    return {
        "analysis": {
            "price_trend": "bullish" if price_change > 0 else "bearish" if price_change < 0 else "neutral",
            "volume_analysis": market_data.get("volume", "Normal"),
            "technical_indicators": market_data,
            "key_factors": ["Price change", "Volume"]
        },
        "recommendation": recommendation,
        "confidence": confidence,
        "reasoning": reasoning
    }

@app.get("/market-summary")
def get_market_summary():
    """
    Get overall market summary
    """
    return {
        "market_status": "open",
        "major_indices": {
            "SP500": {"value": 4500.00, "change": "+0.5%"},
            "NASDAQ": {"value": 14000.00, "change": "+0.8%"},
            "DOW": {"value": 35000.00, "change": "+0.3%"}
        },
        "market_sentiment": "bullish",
        "volatility": "low",
        "last_updated": datetime.now().isoformat()
    }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
