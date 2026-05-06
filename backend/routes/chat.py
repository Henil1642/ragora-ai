"""
Chat/RAG routes
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
import time

from database.db import get_db
from database.models import User, Bot, ChatHistory
from schemas.chat import ChatMessage, ChatResponse, ChatHistoryItem, ChatSource
from services.auth_service import AuthService
from services.rag_service import RAGService
from utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)
auth_service = AuthService()
rag_service = RAGService()


@router.post("/query", response_model=ChatResponse)
async def chat_query(
    message: ChatMessage,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user),
    background_tasks: BackgroundTasks = BackgroundTasks(),
):
    """
    Send a message to bot and get RAG-powered response using Groq
    """
    # Verify bot ownership
    bot = db.query(Bot).filter(
        Bot.id == message.bot_id,
        Bot.user_id == current_user.id,
    ).first()

    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bot not found",
        )

    if not bot.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bot is inactive",
        )

    start_time = time.time()

    try:
        # Get RAG response using Groq
        response_data = await rag_service.generate_response(
            bot_id=message.bot_id,
            query=message.user_message,
            bot=bot,
        )

        processing_time = (time.time() - start_time) * 1000  # milliseconds

        # Parse sources
        sources = []
        for source in response_data.get("sources", []):
            sources.append(
                ChatSource(
                    document_id=source.get("document_id", ""),
                    filename=source.get("filename", ""),
                    content=source.get("content", ""),
                    page=source.get("page"),
                    score=source.get("score", 0.0),
                )
            )

        # Save chat history
        chat_history = ChatHistory(
            bot_id=message.bot_id,
            user_message=message.user_message,
            bot_response=response_data.get("response", ""),
            sources=[s.dict() for s in sources],
            tokens_used=response_data.get("tokens_used"),
            processing_time=processing_time,
        )
        db.add(chat_history)
        db.commit()

        return ChatResponse(
            bot_response=response_data.get("response", ""),
            sources=sources,
            processing_time=processing_time,
            tokens_used=response_data.get("tokens_used"),
        )

    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process query",
        )


@router.get("/{bot_id}/history", response_model=List[ChatHistoryItem])
async def get_chat_history(
    bot_id: str,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user),
):
    """
    Get chat history for a bot
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

    history = (
        db.query(ChatHistory)
        .filter(ChatHistory.bot_id == bot_id)
        .order_by(ChatHistory.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return history


@router.post("/{message_id}/rate")
async def rate_message(
    message_id: str,
    rating: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user),
):
    """
    Rate a chat message (1-5 stars)
    """
    if not 1 <= rating <= 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rating must be between 1 and 5",
        )

    message = db.query(ChatHistory).filter(ChatHistory.id == message_id).first()

    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found",
        )

    # Verify user owns the bot
    bot = db.query(Bot).filter(
        Bot.id == message.bot_id,
        Bot.user_id == current_user.id,
    ).first()

    if not bot:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized",
        )

    message.rating = rating
    db.commit()

    return {"success": True, "rating": rating}