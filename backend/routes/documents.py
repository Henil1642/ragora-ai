"""
Document upload and management routes
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
import os

from database.db import get_db
from database.models import User, Bot, Document
from schemas.document import DocumentResponse, DocumentDetailResponse
from services.auth_service import AuthService
from services.document_service import DocumentService
from utils.logger import get_logger
from config.settings import settings

router = APIRouter()
logger = get_logger(__name__)
auth_service = AuthService()
document_service = DocumentService()


@router.post("/{bot_id}/upload", response_model=DocumentResponse)
async def upload_document(
    bot_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user),
    background_tasks: BackgroundTasks = BackgroundTasks(),
):
    """
    Upload and process a document
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

    # Validate file
    if file.size and file.size > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_PAYLOAD_TOO_LARGE,
            detail="File too large",
        )

    # Check file extension
    allowed_extensions = {".pdf", ".docx", ".txt", ".pptx"}
    file_ext = os.path.splitext(file.filename or "")[1].lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not supported. Allowed: {', '.join(allowed_extensions)}",
        )

    try:
        # Save file and create document record
        doc = await document_service.save_and_process_document(
            file=file,
            bot_id=bot_id,
            db=db,
        )

        # Process in background
        background_tasks.add_task(
            document_service.process_document_async,
            document_id=doc.id,
            bot_id=bot_id,
            file_path=doc.file_path,
        )

        logger.info(f"Document uploaded: {doc.id} for bot {bot_id}")

        return doc

    except Exception as e:
        logger.error(f"Document upload error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload document",
        )


@router.get("/{bot_id}/documents", response_model=List[DocumentResponse])
async def list_documents(
    bot_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user),
):
    """
    List documents for a bot
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

    documents = db.query(Document).filter(Document.bot_id == bot_id).all()

    return documents


@router.get("/{bot_id}/documents/{document_id}", response_model=DocumentDetailResponse)
async def get_document(
    bot_id: str,
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user),
):
    """
    Get document details
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

    document = db.query(Document).filter(
        Document.id == document_id,
        Document.bot_id == bot_id,
    ).first()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    return document


@router.delete("/{bot_id}/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    bot_id: str,
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user),
):
    """
    Delete a document
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

    document = db.query(Document).filter(
        Document.id == document_id,
        Document.bot_id == bot_id,
    ).first()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    # Delete file
    if os.path.exists(document.file_path):
        os.remove(document.file_path)

    db.delete(document)
    db.commit()

    logger.info(f"Document deleted: {document_id}")