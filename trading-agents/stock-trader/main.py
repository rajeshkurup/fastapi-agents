#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Stock Trader AI Agent.
"""

from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
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

class TradeRequest(BaseModel):
    symbol: str
    action: str
    quantity: int
    price: Optional[float] = None
    session_id: str

class TradeResponse(BaseModel):
    trade_id: str
    symbol: str
    action: str
    quantity: int
    price: float
    status: str
    timestamp: str

@app.get("/")
def root():
    return {"message": "Stock Trader Service with LLM", "status": "running"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "agent": "stock-trader"}

@app.post("/execute-trade")
def execute_trade(request: TradeRequest):
    """
    Execute trades with LLM risk assessment
    """

    if request.action == "HOLD":
        return {
            "trade_id": f"HOLD-{datetime.now().timestamp()}",
            "symbol": request.symbol,
            "action": "HOLD",
            "quantity": 0,
            "price": 0.0,
            "status": "NO_ACTION",
            "timestamp": datetime.now().isoformat(),
            "risk_assessment": "No trade executed - HOLD recommendation"
        }

    # Validate action
    if request.action not in ["BUY", "SELL"]:
        return {"error": "Invalid action. Use BUY, SELL, or HOLD"}

    current_price = request.price if request.price else 150.00

    try:
        risk_assessment = assess_trade_risk_with_llm(
            request.symbol,
            request.action,
            request.quantity,
            current_price
        )
    except Exception as e:
        print(f"LLM risk assessment failed: {e}")
        risk_assessment = f"Risk assessment unavailable. Proceeding with {request.action} trade."

    # Generate trade ID
    trade_id = f"{request.action}-{request.symbol}-{int(datetime.now().timestamp())}"

    # Calculate toal value
    total_value = current_price * request.quantity

    # Execute trade
    trade_result = {
        "trade_id": trade_id,
        "symbol": request.symbol,
        "action": request.action,
        "quantity": request.quantity,
        "price": current_price,
        "status": "EXECUTED",
        "timestamp": datetime.now().isoformat(),
        "risk_assessment": risk_assessment,
        "total_value": total_value,
        "portfolio_impact": {
            "cash_impact": -total_value if request.action == "BUY" else total_value,
            "position_change": request.quantity if request.action == "BUY" else -request.quantity
        }
    }

    print(f"Trade executed: {trade_id}")
    print(f"Risk Assessment: {risk_assessment}")

    return trade_result

def assess_trade_risk_with_llm(symbol: str, action: str, quantity: int, price: float) -> str:
    """
    Use LLM to assess trade risk
    """
    total_value = price * quantity

    prompt = f"""You are a risk management expert for stock trading. Assess the risk of this trade:

    Symbol: {symbol}
    Action: {action}
    Quantity: {quantity} shares
    Price per Share: ${price}
    Total Trade Value: ${total_value:,.2f}

    Provide a brief risk assessment (2-3 sentences) covering:
    1. Position sizing appropriateness (is this trade size reasonable?)
    2. Market timing considerations for this {action} order
    3. Key risk factors to monitor

    Keep it concise, actionable, and professional.
    """

    # Initialize Gemini model
    model = GenerativeModel("gemini-2.5-pro")

    response = model.generate_content(prompt)
    return response.text.strip()

@app.get("/trades/history")
def get_trade_history():
    """
    Get recent trade history
    """
    return {
        "trades": [
            {
                "trade_id": "BUY-AAPL-1234567890",
                "symbol": "AAPL",
                "action": "BUY",
                "quantity": 10,
                "price": 150.00,
                "total_value": 1500.00,
                "timestamp": datetime.now().isoformat(),
                "status": "EXECUTED"
            },
            {
                "trade_id": "SELL-TSLA-1234567891",
                "symbol": "TSLA",
                "action": "SELL",
                "quantity": 5,
                "price": 210.00,
                "total_value": 1050.00,
                "timestamp": datetime.now().isoformat(),
                "status": "EXECUTED"
            }
        ],
        "total_trades": 2,
        "last_updated": datetime.now().isoformat()
    }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
