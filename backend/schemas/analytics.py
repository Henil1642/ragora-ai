"""
Pydantic schemas for analytics
"""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class AnalyticsResponse(BaseModel):
    """Analytics response schema"""
    total_queries: int
    successful_queries: int
    failed_queries: int
    success_rate: float
    avg_response_time: Optional[float]
    avg_rating: Optional[float]


class DailyAnalytics(BaseModel):
    """Daily analytics schema"""
    date: datetime
    total_queries: int
    successful_queries: int
    avg_response_time: Optional[float]
    avg_rating: Optional[float]

    class Config:
        from_attributes = True