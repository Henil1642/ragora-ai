"""
Pydantic schemas for documents
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class DocumentBase(BaseModel):
    """Base document schema"""
    filename: str
    file_type: str


class DocumentCreate(DocumentBase):
    """Document creation schema"""
    pass


class DocumentResponse(DocumentBase):
    """Document response schema"""
    id: str
    bot_id: str
    file_size: int
    status: str
    total_chunks: int
    created_at: datetime
    updated_at: datetime
    error_message: Optional[str] = None

    class Config:
        from_attributes = True


class DocumentDetailResponse(DocumentResponse):
    """Document detail response"""
    metadata: Optional[Dict[str, Any]] = None