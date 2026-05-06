"""
Bot management routes
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from database.db import get_db
from database.models import User, Bot
from schemas.bot import BotCreate, BotResponse, BotUpdate, BotDetailResponse
from services.auth_service import AuthService
from utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)
auth_service = AuthService()


@router.post("", response_model=BotResponse, status_code=status.HTTP_201_CREATED)
async def create_bot(
    bot_data: BotCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user),
):
    """
    Create a new bot
    """
    bot = Bot(
        user_id=current_user.id,
        name=bot_data.name,
        description=bot_data.description,
        instructions=bot_data.instructions,
        temperature=bot_data.temperature,
        max_tokens=bot_data.max_tokens,
    )
    db.add(bot)
    db.commit()
    db.refresh(bot)
    logger.info(f"Bot created: {bot.id} by user {current_user.id}")

    return bot


@router.get("", response_model=List[BotResponse])
async def list_bots(
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user),
):
    """
    List all bots for current user
    """
    bots = db.query(Bot).filter(Bot.user_id == current_user.id).all()
    logger.info(f"Listed {len(bots)} bots for user {current_user.id}")

    return bots


@router.get("/{bot_id}", response_model=BotDetailResponse)
async def get_bot(
    bot_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user),
):
    """
    Get bot details
    """
    bot = db.query(Bot).filter(
        Bot.id == bot_id,
        Bot.user_id == current_user.id,
    ).first()

    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bot not found",
        )

    # Get statistics
    total_documents = len(bot.documents)
    total_queries = len(bot.chat_histories)
    last_query = None
    if bot.chat_histories:
        last_query = max(bot.chat_histories, key=lambda x: x.created_at).created_at

    return BotDetailResponse(
        **bot.__dict__,
        total_documents=total_documents,
        total_queries=total_queries,
        last_query_at=last_query,
    )


@router.put("/{bot_id}", response_model=BotResponse)
async def update_bot(
    bot_id: str,
    bot_data: BotUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user),
):
    """
    Update bot
    """
    bot = db.query(Bot).filter(
        Bot.id == bot_id,
        Bot.user_id == current_user.id,
    ).first()

    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bot not found",
        )

    # Update fields
    update_data = bot_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(bot, field, value)

    db.commit()
    db.refresh(bot)
    logger.info(f"Bot updated: {bot_id}")

    return bot


@router.delete("/{bot_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bot(
    bot_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user),
):
    """
    Delete bot
    """
    bot = db.query(Bot).filter(
        Bot.id == bot_id,
        Bot.user_id == current_user.id,
    ).first()

    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bot not found",
        )

    db.delete(bot)
    db.commit()
    logger.info(f"Bot deleted: {bot_id}")