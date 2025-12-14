"""
WebSocket endpoint for real-time stock analysis streaming.
Provides progressive updates as analysis is being generated.
"""
import asyncio
import json
from typing import Dict, Any
from fastapi import WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from loguru import logger

from app.core.database import get_db
from app.services.data_ingestion import data_ingestion_service
from app.services.rag import rag_service
from app.services.redis_cache import redis_cache


class ConnectionManager:
    """Manages WebSocket connections for real-time analysis."""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        """Accept and store WebSocket connection."""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"[WS] Client connected: {client_id}")
    
    def disconnect(self, client_id: str):
        """Remove WebSocket connection."""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info(f"[WS] Client disconnected: {client_id}")
    
    async def send_message(self, client_id: str, message: dict):
        """Send JSON message to specific client."""
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_json(message)
            except Exception as e:
                logger.error(f"[WS] Error sending to {client_id}: {e}")
                self.disconnect(client_id)


manager = ConnectionManager()


async def stream_analysis_progress(
    websocket: WebSocket,
    ticker: str,
    user_id: int = None
) -> Dict[str, Any]:
    """
    Perform stock analysis with real-time progress updates via WebSocket.
    
    Args:
        websocket: WebSocket connection
        ticker: Stock ticker symbol
        user_id: Optional user ID for authenticated requests
        
    Returns:
        Complete analysis result
    """
    try:
        # Send initial status
        await websocket.send_json({
            "type": "status",
            "message": f"Starting analysis for {ticker}...",
            "progress": 0
        })
        
        # Step 1: Check cache (10%)
        await websocket.send_json({
            "type": "progress",
            "step": "cache_check",
            "message": "Checking cache...",
            "progress": 10
        })
        
        cached = redis_cache.get_analysis(ticker)
        if cached:
            await websocket.send_json({
                "type": "status",
                "message": "Analysis retrieved from cache!",
                "progress": 100
            })
            await websocket.send_json({
                "type": "complete",
                "data": cached
            })
            return cached
        
        # Step 2: Fetch stock data (30%)
        await websocket.send_json({
            "type": "progress",
            "step": "fetch_data",
            "message": f"Fetching stock data for {ticker}...",
            "progress": 30
        })
        
        stock_data = await data_ingestion_service.fetch_stock_data(ticker)
        
        await websocket.send_json({
            "type": "progress",
            "step": "data_fetched",
            "message": f"Stock data retrieved: ${stock_data.get('current_price', 'N/A')}",
            "progress": 50
        })
        
        # Step 3: Generate AI analysis (50-90%)
        await websocket.send_json({
            "type": "progress",
            "step": "ai_analysis",
            "message": "Generating AI analysis...",
            "progress": 60
        })
        
        # Send AI processing update
        await websocket.send_json({
            "type": "progress",
            "step": "ai_processing",
            "message": "AI is analyzing market trends...",
            "progress": 75
        })
        
        # Prepare query for RAG analysis
        rag_query = f"Provide detailed stock analysis for {ticker}"
        
        # Generate analysis using RAG service (synchronous, not async)
        analysis = await rag_service.generate_analysis(rag_query, ticker=ticker)
        
        # Step 4: Finalizing (95%)
        await websocket.send_json({
            "type": "progress",
            "step": "finalizing",
            "message": "Finalizing analysis...",
            "progress": 95
        })
        
        # Cache result
        redis_cache.set_analysis(ticker, analysis)
        
        # Step 5: Complete (100%)
        await websocket.send_json({
            "type": "status",
            "message": "Analysis complete!",
            "progress": 100
        })
        
        await websocket.send_json({
            "type": "complete",
            "data": analysis
        })
        
        return analysis
        
    except Exception as e:
        logger.error(f"[WS] Analysis error for {ticker}: {e}")
        await websocket.send_json({
            "type": "error",
            "message": f"Analysis failed: {str(e)}"
        })
        raise


async def websocket_endpoint(
    websocket: WebSocket,
    ticker: str,
    db: Session = Depends(get_db)
):
    """
    WebSocket endpoint for real-time stock analysis.
    
    URL: ws://localhost:8000/ws/stocks/{ticker}/analysis
    
    Message Format:
    - Client sends: {"action": "analyze"}
    - Server sends: Multiple progress updates + final result
    """
    client_id = f"{ticker}_{id(websocket)}"
    
    try:
        # Accept connection
        await manager.connect(websocket, client_id)
        
        # Send welcome message
        await websocket.send_json({
            "type": "connected",
            "message": f"Connected to analysis stream for {ticker}",
            "ticker": ticker
        })
        
        # Wait for client messages
        while True:
            data = await websocket.receive_json()
            action = data.get("action")
            
            if action == "analyze":
                # Get user from token if provided
                user_id = None
                if "token" in data:
                    user_id = data.get("user_id")
                
                # Stream analysis with progress updates
                await stream_analysis_progress(websocket, ticker, user_id)
                
            elif action == "ping":
                # Keepalive
                await websocket.send_json({"type": "pong"})
                
            else:
                await websocket.send_json({
                    "type": "error",
                    "message": f"Unknown action: {action}"
                })
    
    except WebSocketDisconnect:
        manager.disconnect(client_id)
        logger.info(f"[WS] Client disconnected: {client_id}")
    
    except Exception as e:
        logger.error(f"[WS] Error: {e}")
        manager.disconnect(client_id)
        try:
            await websocket.send_json({
                "type": "error",
                "message": str(e)
            })
        except:
            pass
