#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Session Manager for Orchestrator.
"""

from google.cloud import firestore
from datetime import datetime
from typing import Optional, Dict, List
import json

class SessionManager:
    """
    Manages trading sessions using Google Cloud Firestore
    """

    def __init__(self, project_id: str):
        """Initialize Firestore Client"""
        self.db = firestore.Client(project=project_id)
        self.sessions_collection = self.db.collection("trading_sessions")
        self.analysis_collection = self.db.collection("analysis_history")
        self.trades_collection = self.db.collection("trade_hostory")

    def create_session(self, session_id: str, user_id: str, initial_data: Dict) -> Dict:
        """Create a new trading session"""
        session_data = {
            "session_id": session_id,
            "user_id": user_id,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "status": "active",
            "initial_data": initial_data,
            "workflow_steps": [],
            "metadata": {}
        }

        self.sessions_collection.document(session_id).set(session_data)
        print(f"[SessionManager] Created session: {session_id}")

        return session_data
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """Retrieve a session by Id"""
        doc = self.sessions_collection.document(session_id).get()

        if doc.exists:
            print(f"[SessionManager] Retrieved session: {session_id}")
            return doc.to_dict()
        else:
            print(f"[SessionManager] Session not found: {session_id}")
            return None
        
    def update_session(self, session_id: str, update_data: Dict) -> bool:
        """Update session with new data"""
        try:
            self.sessions_collection.document(session_id).update({
                "updated_at": datetime.now(),
                **update_data
            })
            print(f"[SessionManager] Updated session: {session_id}")
            return True
        except Exception as e:
            print(f"[SessionManager] Error updating session {session_id}: {e}")
            return False
        
    def add_workflow_step(self, session_id: str, step_data: Dict) -> bool:
        """Add a workflow step to the session"""
        try:
            step_with_timestamp = {
                **step_data,
                "timestamp": datetime.now()
            }

            self.sessions_collection.document(session_id).update({
                "workflow_steps": firestore.ArrayUnion([step_with_timestamp]),
                "updated_at": datetime.now()
            })

            print(f"[SessionManager] Added workflow step to session: {session_id}")
            return True
        except Exception as e:
            print(f"[SessionManager] Error adding workflow step: {e}")
            return False
        
    def save_analysis(self, session_id: str, symbol: str, analysis_data: Dict) -> str:
        """Save analysis result to Firestore"""
        analysis_id = f"{session_id}-{symbol}-{int(datetime.now().timestamp())}"

        analysis_doc = {
            "analysis_id": analysis_id,
            "session_id": session_id,
            "symbol": symbol,
            "analysis_data": analysis_data,
            "created_at": datetime.now()
        }

        self.analysis_collection.document(analysis_id).set(analysis_doc)
        print(f"[SessionManager] Saved analysis: {analysis_id}")

        return analysis_id
    
    def save_trade(self, session_id: str, trade_data: Dict) -> str:
        """Save trade execution to Firestore"""
        trade_id = trade_data.get("trade_id", f"trade-{int(datetime.now().timestamp())}")

        trade_doc = {
            "trade_id": trade_id,
            "session_id": session_id,
            "trade_data": trade_data,
            "created_at": datetime.now()
        }

        self.trades_collection.document(trade_id).set(trade_doc)
        print(f"[SessionManager] Saved trade: {trade_id}")

        return trade_id
    
    def get_user_sessions(self, user_id: str, limit: int = 10) -> List[Dict]:
        """Get all sessions for a user"""
        sessions = (
            self.sessions_collection
            .where("user_id", "==", user_id)
            .order_by("created_at", direction=firestore.Query.DESCENDING)
            .limit(limit)
            .stream()
        )

        results = [doc.to_dict() for doc in sessions]
        print(f"[SessionManager] Retrieved {len(results)} sessions for user: {user_id}")

        return results
    
    def get_session_analysis_history(self, session_id: str) -> List[Dict]:
        """Get all analysis results for a session"""
        analyses = (
            self.analysis_collection
            .where("session_id", "==", session_id)
            .order_by("created_at", direction=firestore.Query.DESCENDING)
            .stream()
        )

        results = [doc.to_dict() for doc in analyses]
        print(f"[SessionManager] {len(results)} analyses for session: {session_id}")

        return results
    
    def get_session_trades(self, session_id: str) -> List[Dict]:
        """Get all trades for a session"""
        trades = (
            self.trades_collection
            .where("session_id", "==", session_id)
            .order_by("created_at", direction=firestore.Query.DESCENDING)
            .stream()
        )

        results = [doc.to_dict() for doc in trades]
        print(f"[SessionManager] Retrieved {len(results)} trades for session: {session_id}")

        return results

    def get_user_trade_history(self, user_id: str, limit: int = 20) -> List[Dict]:
        """Get trade history for a user across all sessions"""
        user_sessions = self.get_user_sessions(user_id, limit=100)
        session_ids = [s["session_id"] for s in user_sessions]

        if not session_ids:
            print(f"[SessionManager] No Sessions found for {user_id}")
            return []
        
        all_trades = []
        for session_id in session_ids:
            trades = self.get_session_trades(session_id)
            all_trades.append(trades)

        print(f"[SessionManager] Total Trades in DB: {len(all_trades)}")

        def get_sort_key(trade):
            """Safely get created_at for sorting"""
            if not isinstance(trade, dict):
                return datetime.min
        
            created_at = trade.get("created_at")

            if isinstance(created_at, datetime):
                return created_at
        
            return datetime.min

        all_trades.sort(key=get_sort_key, reverse=True)
        results = all_trades[:limit]

        return results

    def close_session(self, session_id: str) -> bool:
        """Close a session"""
        return self.update_session(session_id, {"status": "closed"})
    