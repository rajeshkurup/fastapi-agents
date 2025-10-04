#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Trading Orchestrator AI Agent.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx
import os
import uvicorn
from typing import Optional, List
from datetime import datetime
import vertexai
from vertexai.preview.generative_models import GenerativeModel
import json
from sessionmanager import SessionManager

app = FastAPI()

# Init Vertex AI
PROJECT_ID = os.getenv("PROJECT_ID", "")
LOCATION = os.getenv("LOCATION", "us-central1")

session_manager = None
if PROJECT_ID:
    vertexai.init(project=PROJECT_ID, location=LOCATION)
    try:
        session_manager = SessionManager(PROJECT_ID)
        print(f"Session Manager initialized")
    except Exception as e:
        print(f"Session Manager initialization failed: {e}")

# Get service URLs from environment variables
MARKET_ANALYST_URL = os.getenv("MARKET_ANALYST_URL", "")
STOCK_TRADER_URL = os.getenv("STOCK_TRADER_URL", "")

class TradingRequest(BaseModel):
    symbol: str
    analysis_type: str = "technical"
    quantity: int = 100
    user_id: str
    session_id: Optional[str] = None
    auto_execute: bool = True

class NaturalLanguageRequest(BaseModel):
    query: str
    user_id: str
    session_id: Optional[str] = None

@app.get("/")
def root():
    return {
        "message": "Intelliget Trading Orchestrator Service with LLM support",
        "status": "running",
        "session_manager_enabled": session_manager is not None,
        "services": {
            "market_analyst": MARKET_ANALYST_URL,
            "stock_trader": STOCK_TRADER_URL
        },
        "capabilities": [
            "Trading workflow orchestration",
            "Natural language trading commands",
            "Intellegent agent coordination",
            "Multi-step decision making"
        ],
        "endpoints": [
            "GET /health",
            "POST /trading-workflow",
            "POST /natural-language-trading",
            "GET /services/health",
            "GET /sessions/{{session_id}}",
            "GET /users/{{user_id}}/sessions",
            "GET /users/{{user_id}}/trades"            
        ]
    }

@app.get("/health")
def health_check():
    return {"status": "healthy", "agent": "trading-orchestrator"}

@app.post("/trading-workflow")
async def orchestrate_trading(request: TradingRequest):
    """
    Orchestrates the complete trading workflow with LLM intelegence
    """

    session_id = request.session_id or f"session-{request.user_id}-{request.symbol}-{int(datetime.now().timestamp())}"

    # Create session in Firestore
    if session_manager:
        session_manager.create_session(
            session_id=session_id,
            user_id=request.user_id,
            initial_data={
                "symbol": request.symbol,
                "quantiry": request.quantity,
                "auto_execute": request.auto_execute
            }
        )

        session_manager.add_workflow_step(session_id, {
            "step": "workflow_started",
            "data": request.model_dump()
        })

    if not MARKET_ANALYST_URL or not STOCK_TRADER_URL:
        raise HTTPException(
            status_code=500,
            detail="Service URLs not configured. Set MARKET_ANALYST_URL and STOCKE_TRADER_URL environment variables."
        )
    
    print(f"[{session_id}] Starting intelligent trading workflow for {request.symbol}")

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:

            # Step 1: Get market analysis from Market Analyst
            print(f"[{session_id}] Step 1: Requesting LLM powered analysis...")

            if session_manager:
                session_manager.add_workflow_step(session_id, {
                    "step": "analysis_requested",
                    "symbol": request.symbol
                })
            
            analysis_response = await client.post(
                f"{MARKET_ANALYST_URL}/analyze",
                json={
                    "symbol": request.symbol,
                    "analysis_type": request.analysis_type,
                    "session_id": session_id
                }
            )
            
            analysis_response.raise_for_status()
            analysis_data = analysis_response.json()

            print(f"[{session_id}] Analysis completed. Recommendation: {analysis_data['recommendation']} (confidence: {analysis_data['confidence']})")
            print(f"[{session_id}] LLM Reasoning: {analysis_data.get('llm_reasoning', 'N/A')}")

            # Save analysis to Firestore
            if session_manager:
                analysis_id = session_manager.save_analysis(
                    session_id=session_id,
                    symbol=request.symbol,
                    analysis_data=analysis_data
                )

                session_manager.add_workflow_step(session_id, {
                    "step": "analysis_completed",
                    "analysis_id": analysis_id,
                    "recommendation": analysis_data.get("recommendation")
                })

            # Step 2: Use LLM to decide if we should proceed with the trade
            should_execute = decide_execution_with_llm(
                analysis_data,
                request.quantity,
                request.auto_execute
            )

            print(f"[{session_id}] LLM Decision: {'EXECUTE' if should_execute else 'SKIP'} trade")

            # Step 3: Execute trade if LLM approves and auto_execute is True
            trade_data = None
            workflow_status = "ANALYSIS_ONLY"

            if should_execute and request.auto_execute:
                print(f"[{session_id}] Step 2: Executing trade with LLM risk assessment...")

                if session_manager:
                    session_manager.add_workflow_step(session_id, {
                        "step": "trade_requested",
                        "action": analysis_data.get("recommendation")
                    })

                trade_response = await client.post(
                    f"{STOCK_TRADER_URL}/execute-trade",
                    json={
                        "symbol": request.symbol,
                        "action": analysis_data["recommendation"],
                        "quantity": request.quantity,
                        "price": None,
                        "session_id": session_id
                    }
                )

                trade_response.raise_for_status()
                trade_data = trade_response.json()

                # Save analysis to Firestore
                if session_manager:
                    trade_id = session_manager.save_trade(
                        session_id=session_id,
                        trade_data=trade_data
                    )

                    session_manager.add_workflow_step(session_id, {
                        "step": "trade_executed",
                        "trade_id": trade_id,
                        "status": trade_data.get("status")
                    })

                workflow_status = "COMPLETED"
                print(f"[{session_id}] Trade executed with risk assessment")

            elif not request.auto_execute:
                workflow_status = "ANALYSIS_ONLY"
                print(f"[{session_id}] Auto-execute is disabled, analysis only")

            else:
                workflow_status = "EXECUTION_DECLINED"
                print(f"[{session_id}] LLM declined trade execution")

            # Update sesion status
            if session_manager:
                session_manager.update_session(session_id, {
                    "status": "completed",
                    "workflow_status": workflow_status
                })

            # Step 4: Generate intellegent summary with LLM
            summary = generate_workflow_summary(
                request.symbol,
                analysis_data,
                trade_data,
                workflow_status
            )

            return {
                "session_id": session_id,
                "symbol": request.symbol,
                "user_id": request.user_id,
                "analysis": analysis_data,
                "trade_result": trade_data,
                "workflow_status": workflow_status,
                "timestamp": datetime.now().isoformat(),
                "summary": summary
            }

    except Exception as e:
        print(f"[{session_id}] Unexpected Error: {e}")
        raise HTTPException(status_code=500, detail=f"Workflow orchestration error: {str(e)}")

@app.post("/natural-language-trading")
async def natural_language_trading(request: NaturalLanguageRequest):
    """
    Process natural language trading commands using LLM
    Examples:
    - "Should I buy 100 shares of Apple?"
    - "Analyze Tesla and tell me if it's a good buy"
    - "What's your recommendation for google stick?"
    """

    session_id = request.session_id or f"nl-{request.user_id}-{int(datetime.now().timestamp())}"
    
    print(f"[{session_id}] Processing natural language query: {request.query}")

    try:
        # Use LLM to parse the intent and extract trading parameters
        parsed_intent = parse_trading_intent_with_llm(request.query)

        print(f"[{session_id}] Parsed intent: {json.dumps(parsed_intent, indent=2)}")

        if parsed_intent.get("action") == "analyze" and parsed_intent.get("symbol"):
            # Execute analysis workflow
            trading_request = TradingRequest(
                symbol=parsed_intent["symbol"],
                analysis_type=parsed_intent.get("analysis_type", "technical"),
                quantity=parsed_intent.get("quantity", 100),
                user_id=request.user_id,
                session_id=session_id,
                auto_execute=parsed_intent.get("auto_execute", False)
            )

            result = await orchestrate_trading(trading_request)

            # Generate natural language response
            nl_response = generate_natural_language_response(request.query, result)

            return {
                "query": request.query,
                "parsed_intent": parsed_intent,
                "workflow_result": result,
                "natural_language_response": nl_response,
                "session_id": session_id
            }
        
        else:
            return {
                "query": request.query,
                "response": "I can help you analyze stocks and make trading decisions. Please ask about a specific stock symbol.",
                "session_id": session_id
            }
    
    except Exception as e:
        print(f"[{session_id}] Error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Natural language processing error: {str(e)}"
        )
    
def decide_execution_with_llm(analysis_data: dict, quantity: int, auto_execute: bool) -> bool:
    """
    Use LLM to decide if trade should be executed based on analysis
    """
    if not auto_execute:
        return False
    
    try:
        prompt = f"""You are trading decision engine. Based on the following analysis, decide if we should execute the trade.

        Analysis Data:
        - Recommendation: {analysis_data.get('recommendation')}
        - Confidence: {analysis_data.get('confidence')}
        - Reasoning: {analysis_data.get('llm_reasoning', 'Not provided')}
        - Quantity: {quantity} shares

        Rules:
        1. Only execute BUY or SELL if confidence is above 0.7
        2. Never execute HOLD actions
        3. Consider the reasoning provided

        Respond with ONLY "YES" or "NO" and a brief reason (one sentence).
        Format: YES/NO - reason
        """

        model = GenerativeModel("gemini-2.5-pro")
        response = model.generate_content(prompt)
        response_text = response.text.strip()

        print(f"LLM Execution Decision: {response_text}")

        should_execute = response_text.upper().startswith("YES")
        return should_execute
    
    except Exception as e:
        print(f"LLM Decision failed: {e}")
        # Fallback: execute if confidence > 0.7 and not HOLD
        return (
            analysis_data.get('confidence', 0) > 0.7 and analysis_data.get('recommendation') != 'HOLD'
        )

def generate_workflow_summary(symbol: str, analysis_data: dict, trade_data: Optional[dict], status: str) -> str:
    """
    Generate intellegent summary of the workflow using LLM
    """
    try:
        prompt = f"""Generate a concise executive summary (2-3 sentences) of this trading workflow:

        Stock: {symbol}
        Analysis Recommendation: {analysis_data.get('recommendation')}
        Analysis Confidence: {analysis_data.get('confidence')}
        Analysis Reasoning: {analysis_data.get('llm_reasoning', 'Not provided')}
        Trade Status: {status}
        Trade Executed: {'Yes' if trade_data else 'No'}

        If trade was executed:
        - Action: {trade_data.get('action') if trade_data else 'N/A'}
        - Quantity {trade_data.get('quantity') if trade_data else 'N/A'}
        - Risk Assessment {trade_data.get('risk_assessment') if trade_data else 'N/A'}

        Provide a clean, proffessional summary for the use.
        """

        model = GenerativeModel("gemini-2.5-pro")
        response = model.generate_content(prompt)

        return response.text.strip()
    
    except Exception as e:
        print(f"Summary generation failed: {e}")
        return f"Analyzed {symbol}: {analysis_data.get('recommendation')} recommendation. Status: {status}"

def parse_trading_intent_with_llm(query: str) -> dict:
    """
    Parse natural language query to extract trading untent
    """

    try:
        prompt = f"""Parse this trading query and extract the intent and parameters.

        Qurery: "{query}"

        Extract:
        1. Stock symbol (if mentioned)
        2. Action: "analyze", "buy", "sell", or "unknown"
        3. Quantity (if mentioned, otherwise default to 100)
        4. Analysis type: "technical", "fundamental", or "sentiment"
        5. Auto-execute: true is use wants to execute immediately, false if just asking for analysis

        Respond ONLY with valid JSON:
        {{
            "symbol": "SYMBOL or null",
            "action": "analyze/buy/sell/unknown",
            "quantity": 100,
            "analysis_type": "technical",
            "auto_execute": false
        }}
        """

        model = GenerativeModel("gemini-2.5-pro")
        response = model.generate_content(prompt)
        response_text = response.text.strip()

        # Extract JSON from response (handle markdown code blocks)
        if "```json" in response_text:
            json_str = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            json_str = response_text.split("```")[1].split("```")[0].strip()
        else:
            json_str = response_text

        return json.loads(json_str)
    
    except Exception as e:
        print(f"Intent parsing failed: {e}")
        return {
            "symbol": None,
            "action": "unknown",
            "quantity": 100,
            "analysis_type": "technical",
            "auto_execute": False
        }

def generate_natural_language_response(query: str, workflow_result: dict) -> str:
    """
    Generate natural language response to user query
    """

    try:
        prompt = f"""Generate a natural, conversational response to the user's query based on the workflow result.

        User Query: "{query}

        Workflow Result:
        - Symbol: {workflow_result.get('symbol')}
        - Recommendation: {workflow_result.get('analysis', {}).get('recommendation')}
        - Confidence: {workflow_result.get('analysis', {}).get('confidence')}
        - Status: {workflow_result.get('workflow_status')}
        - Summary: {workflow_result.get('summary')}

        Provide a friendly, clear response (2-4 sentences) that:
        1. Answers their question directly
        2. Mentions the key recommendation
        3. Provides actionable insight

        Be conversational but proffessional.
        """

        model = GenerativeModel("gemini-2.5-pro")
        response = model.generate_content(prompt)

        return response.text.strip()
    
    except Exception as e:
        print(f"NL response generation failed: {e}")
        return f"Based on the analysis, I recommend {workflow_result.get('analysis', {}).get('recommendation')} for {workflow_result.get('symbol')}."

@app.get("/sessions/{session_id}")
async def get_session(session_id: str):
    """Get session details"""
    if not session_manager:
        raise HTTPException(status_code=503, detail="Session Manager not available")

    session = session_manager.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    analyses = session_manager.get_session_analysis_history(session_id)
    trades = session_manager.get_session_trades(session_id)

    return {
        "session": session,
        "analyses": analyses,
        "trades": trades
    }

@app.get("/users/{user_id}/sessions")
async def get_user_sessions(user_id: str, limit: int = 10):
    """Get all sessions of a user"""

    if not session_manager:
        raise HTTPException(status_code=503, detail="Session Manager not available")

    sessions = session_manager.get_user_sessions(user_id, limit=limit)

    return {
        "user_id": user_id,
        "total_sessions": len(sessions),
        "sessions": sessions
    }

@app.get("/users/{user_id}/trades")
async def get_user_trades(user_id: str, limit: int = 20):
    """Get trade history of a user"""

    if not session_manager:
        raise HTTPException(status_code=503, detail="Session Manager not available")

    trades = session_manager.get_user_trade_history(user_id, limit=limit)

    return {
        "user_id": user_id,
        "total_trades": len(trades),
        "trades": trades
    }

@app.get("/services/health")
async def check_services_health():
    """
    Check health of all connected services
    """
    health_status = {
        "orchestrator": "healthy",
        "market_analyst": "unknown",
        "stock_trader": "unknown",
        "timestamp": datetime.now().isoformat()
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            if MARKET_ANALYST_URL:
                try:
                    response = await client.get(f"{MARKET_ANALYST_URL}/health")
                    health_status["market_analyst"] = "healthy" if response.status_code == 200 else "unhealthy"
                except:
                    health_status["markey_analyst"] = "unreachable"

            if STOCK_TRADER_URL:
                try:
                    response = await client.get(f"{STOCK_TRADER_URL}/health")
                    health_status["stock_trader"] = "healthy" if response.status_code == 200 else "unhealthy"
                except:
                    health_status["stock_trader"] = "unreachable"
    
    except Exception as e:
        health_status["error"] = str(e)

    return health_status

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
