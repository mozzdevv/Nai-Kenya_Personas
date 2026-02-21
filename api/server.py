"""
FastAPI Server
REST API + WebSocket for dashboard.
Production-ready with security hardening.
"""

from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import List, Optional, Dict, Union, Any
from datetime import timedelta
import asyncio
import json
import logging
import os

from .database import DashboardQueries, init_db
from .auth import (
    Token, User, authenticate_user, create_access_token, 
    verify_token, ACCESS_TOKEN_EXPIRE_MINUTES
)
from .security import apply_security_middleware, validate_production_config

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Nairobi Bot Dashboard API",
    description="Monitoring API for Nairobi Swahili X Persona Bots",
    version="1.0.0",
    docs_url="/docs" if os.getenv("PRODUCTION", "false").lower() != "true" else None,
    redoc_url="/redoc" if os.getenv("PRODUCTION", "false").lower() != "true" else None,
)

# Apply security middleware (rate limiting, headers, CORS, logging)
apply_security_middleware(app)

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")



# WebSocket connection manager
class ConnectionManager:
    """Manage WebSocket connections for real-time updates."""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
    
    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients."""
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass


manager = ConnectionManager()


# Dependency: Get current user
async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """Validate token and return current user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    token_data = verify_token(token)
    if token_data is None:
        raise credentials_exception
    return User(username=token_data.username)


# ============ Auth Endpoints ============

@app.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login and get access token."""
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    """Get current user info."""
    return current_user


# ============ Dashboard Endpoints ============

@app.get("/posts")
async def get_posts(
    limit: int = 50,
    current_user: User = Depends(get_current_user)
):
    """Get recent posts."""
    return DashboardQueries.get_recent_posts(limit)


@app.get("/stats")
async def get_stats(current_user: User = Depends(get_current_user)):
    """Get post statistics."""
    return DashboardQueries.get_post_stats()


@app.get("/rag")
async def get_rag_activity(
    limit: int = 50,
    current_user: User = Depends(get_current_user)
):
    """Get RAG activity log."""
    return DashboardQueries.get_rag_activity(limit)


@app.get("/routing")
async def get_routing_stats(current_user: User = Depends(get_current_user)):
    """Get LLM routing statistics (for pie chart)."""
    stats = DashboardQueries.get_llm_routing_stats()
    # Ensure both models are present even if count is 0
    return {
        "grok": stats.get("grok", 0),
        "claude": stats.get("claude", 0)
    }


@app.get("/routing/history")
async def get_routing_history(
    limit: int = 50,
    current_user: User = Depends(get_current_user)
):
    """Get LLM routing decision history."""
    return DashboardQueries.get_llm_routing_history(limit)


@app.get("/errors")
async def get_errors(
    limit: int = 100,
    level: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get error logs."""
    return DashboardQueries.get_errors(limit, level)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/validation/config")
async def get_validation_config(current_user: User = Depends(get_current_user)):
    """Get validation rules and parameters."""
    from validation.content_validator import (
        APPROVED_HASHTAGS, AI_ENGLISH_FRAMERS, FORMAL_CONNECTORS,
        SWAHILI_SHENG_MARKERS
    )
    return {
        "approved_hashtags": sorted(list(APPROVED_HASHTAGS)),
        "ai_patterns": AI_ENGLISH_FRAMERS,
        "formal_connectors": FORMAL_CONNECTORS,
        "language_markers": {
            "swahili_sheng": sorted(list(SWAHILI_SHENG_MARKERS))[:80],
        },
        "scoring_rules": [
            {"name": "Anti-Patterns", "weight": "Hard/Soft Deductions", "descr": "Repetition, AI-isms, formal connectors, over-length."},
            {"name": "Style Authenticity", "weight": "Score Based", "descr": "Code-switching ratio, word length, punctuation density."},
            {"name": "Contextual Fit", "weight": "8pt Deduction", "descr": "Time-of-day mismatch (e.g. morning talk at night)."}
        ]
    }


# ============ WebSocket for Real-time Updates ============

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates."""
    # Verify token from query parameter
    token = websocket.query_params.get("token")
    if not token or not verify_token(token):
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive, receive any client messages
            data = await websocket.receive_text()
            # Could handle client commands here if needed
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# Function to broadcast updates (called from bot)
async def broadcast_update(update_type: str, data: dict):
    """Broadcast an update to all connected dashboard clients."""
    await manager.broadcast({
        "type": update_type,
        "data": data,
    })


# ============ Startup/Shutdown ============

@app.on_event("startup")
async def startup_event():
    """Initialize on startup."""
    init_db()
    logger.info("Dashboard API started")



class BotLogic(BaseModel):
    kamau: Dict[str, Any]
    wanjiku: Dict[str, Any]
    topics: Dict[str, List[str]]
    routing_triggers: Dict[str, List[str]]
    config: Dict[str, Any]

@app.get("/knowledge")
async def get_knowledge(
    current_user: User = Depends(get_current_user),
    limit: int = 100
):
    """Get knowledge base items."""
    return DashboardQueries.get_knowledge_base(limit)

@app.get("/logic", response_model=BotLogic)
async def get_bot_logic(
    current_user: User = Depends(get_current_user)
):
    """Get bot logic and configuration."""
    from config import settings, TOPICS
    from personas import get_personas
    from llm.router import CLAUDE_TRIGGERS
    from dataclasses import asdict
    
    kamau, wanjiku = get_personas()
    
    return {
        "kamau": asdict(kamau),
        "wanjiku": asdict(wanjiku),
        "topics": TOPICS,
        "routing_triggers": CLAUDE_TRIGGERS,
        "config": {
            "loop_interval_hours": settings.loop_interval_hours,
            "dry_run": settings.dry_run,
            "pinecone_index": settings.pinecone_index_name,
            "grok_model": "grok-4-fast",
            "claude_model": "claude-3-5-sonnet-20240620"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
