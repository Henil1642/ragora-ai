"""
Pydantic schemas for chat
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class ChatMessage(BaseModel):
    """Chat message schema"""
    user_message: str = Field(..., min_length=1)
    bot_id: str


class ChatSource(BaseModel):
    """Chat source schema"""
    document_id: str
    filename: str
    content: str
    page: Optional[int] = None
    score: float


class ChatResponse(BaseModel):
    """Chat response schema"""
    bot_response: str
    sources: List[ChatSource]
    processing_time: float
    tokens_used: Optional[int] = None


class ChatHistoryItem(BaseModel):
    """Chat history item schema"""
    id: str
    user_message: str
    bot_response: str
    sources: List[Dict[str, Any]]
    created_at: datetime
    rating: Optional[int] = None

    class Config:
        from_attributes = True