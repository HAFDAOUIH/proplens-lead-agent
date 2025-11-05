from enum import Enum
from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class Route(str, Enum):
    rag = "rag"
    t2sql = "t2sql"
    clarify = "clarify"


class AgentState(BaseModel):
    query: str
    route: Optional[Route] = None
    intent: Optional[str] = None
    confidence: Optional[float] = None
    # Conversation history (last 3 queries for context)
    history: Optional[List[str]] = None
    # T2SQL
    sql: Optional[str] = None
    rows: Optional[List[Dict[str, Any]]] = None
    columns: Optional[List[str]] = None
    # RAG
    answer: Optional[str] = None
    sources: Optional[List[Dict[str, Any]]] = None
    # Errors
    error: Optional[str] = None


