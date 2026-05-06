"""
Document processing service
"""

import os
import shutil
from fastapi import UploadFile
from sqlalchemy.orm import Session
from pathlib import Path

from database.models import Document
from config.settings import settings
from utils.logger import get_logger

logger = get_logger(__name__)


class DocumentService:
    """Document processing service"""

    async def save_and_process_document(
        self,
        file: UploadFile,
        bot_id: str,
        db: Session,
    ) -> Document:
        """
        Save uploaded file and create document record
        """
        # Create upload directory
        upload_dir = Path(settings.UPLOAD_DIR) / bot_id
        upload_dir.mkdir(parents=True, exist_ok=True)

        # Save file
        file_path = upload_dir / (file.filename or "document")
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        # Get file type
        file_ext = Path(file.filename or "").suffix.lower().lstrip(".")

        # Create document record
        document = Document(
            bot_id=bot_id,
            filename=file.filename or "document",
            file_path=str(file_path),
            file_type=file_ext,
            file_size=len(content) if content else 0,
            status="pending",
        )

        db.add(document)
        db.commit()
        db.refresh(document)

        logger.info(f"Document saved: {document.id}")

        return document

    async def process_document_async(
        self,
        document_id: str,
        bot_id: str,
        file_path: str,
    ):
        """
        Process document asynchronously
        """
        logger.info(f"Processing document: {document_id}")