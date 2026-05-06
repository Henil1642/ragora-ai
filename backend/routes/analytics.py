"""
Analytics routes
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from typing import List

from database.db import get_db
from database.models import User, Bot, ChatHistory, Analytics
from schemas.analytics import AnalyticsResponse, DailyAnalytics
from services.auth_service import AuthService
from utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)
auth_service = AuthService()


@router.get("/{bot_id}/summary", response_model=AnalyticsResponse)
async def get_analytics_summary(
    bot_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user),
):
    """
    Get analytics summary for a bot
    """
    # Verify bot ownership
    bot = db.query(Bot).filter(
        Bot.id == bot_id,
        Bot.user_id == current_user.id,
    ).first()

    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bot not found",
        )

    # Get chat history
    history = db.query(ChatHistory).filter(ChatHistory.bot_id == bot_id).all()

    total_queries = len(history)
    successful_queries = len([h for h in history if h.bot_response])
    failed_queries = total_queries - successful_queries

    success_rate = (
        (successful_queries / total_queries * 100) if total_queries > 0 else 0
    )

    avg_response_time = None
    if history:
        times = [h.processing_time for h in history if h.processing_time]
        if times:
            avg_response_time = sum(times) / len(times)

    avg_rating = None
    ratings = [h.rating for h in history if h.rating]
    if ratings:
        avg_rating = sum(ratings) / len(ratings)

    return AnalyticsResponse(
        total_queries=total_queries,
        successful_queries=successful_queries,
        failed_queries=failed_queries,
        success_rate=success_rate,
        avg_response_time=avg_response_time,
        avg_rating=avg_rating,
    )


@router.get("/{bot_id}/daily", response_model=List[DailyAnalytics])
async def get_daily_analytics(
    bot_id: str,
    days: int = 7,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user),
):
    """
    Get daily analytics for last N days
    """
    # Verify bot ownership
    bot = db.query(Bot).filter(
        Bot.id == bot_id,
        Bot.user_id == current_user.id,
    ).first()

    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bot not found",
        )

    # Get history from last N days
    start_date = datetime.utcnow() - timedelta(days=days)
    history = (
        db.query(ChatHistory)
        .filter(
            ChatHistory.bot_id == bot_id,
            ChatHistory.created_at >= start_date,
        )
        .all()
    )

    # Group by date
    daily_data = {}
    for chat in history:
        date_key = chat.created_at.date()
        if date_key not in daily_data:
            daily_data[date_key] = {
                "total": 0,
                "successful": 0,
                "times": [],
                "ratings": [],
            }

        daily_data[date_key]["total"] += 1
        if chat.bot_response:
            daily_data[date_key]["successful"] += 1
        if chat.processing_time:
            daily_data[date_key]["times"].append(chat.processing_time)
        if chat.rating:
            daily_data[date_key]["ratings"].append(chat.rating)

    # Convert to response
    result = []
    for date, data in sorted(daily_data.items()):
        avg_time = sum(data["times"]) / len(data["times"]) if data["times"] else None
        avg_rating = (
            sum(data["ratings"]) / len(data["ratings"]) if data["ratings"] else None
        )

        result.append(
            DailyAnalytics(
                date=datetime.combine(date, datetime.min.time()),
                total_queries=data["total"],
                successful_queries=data["successful"],
                avg_response_time=avg_time,
                avg_rating=avg_rating,
            )
        )

    return result