"""
Pydantic schemas for bots
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class BotBase(BaseModel):
    """Base bot schema"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    instructions: Optional[str] = None
    temperature: float = Field(default=0.7, ge=0.0, le=1.0)
    max_tokens: int = Field(default=500, ge=100, le=4000)


class BotCreate(BotBase):
    """Bot creation schema"""
    pass


class BotUpdate(BaseModel):
    """Bot update schema"""
    name: Optional[str] = None
    description: Optional[str] = None
    instructions: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None


class BotResponse(BotBase):
    """Bot response schema"""
    id: str
    user_id: str
    is_active: bool
    embedding_model: str
    llm_model: str
    vector_store_path: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BotDetailResponse(BotResponse):
    """Bot detail response with stats"""
    total_documents: int = 0
    total_queries: int = 0
    last_query_at: Optional[datetime] = None