"""
LLM Context Schema
"""

from pydantic import BaseModel
from typing import List, Dict, Any


class LLMContext(BaseModel):
    """Context provided to LLM"""
    signal_data: Dict[str, Any]
    scenarios: List[Dict[str, Any]]
    risk_assessment: Dict[str, Any]
    sentiment_context: Dict[str, Any] = {}
    relative_strength: Dict[str, Any] = {}
    existing_rag_context: str = ""
