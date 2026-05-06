"""
SQLAlchemy models for Ragora AI
"""

from sqlalchemy import Column, String, Integer, DateTime, Boolean, Float, Text, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()


class User(Base):
    """User model"""

    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, nullable=False, index=True)
    full_name = Column(String)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    bots = relationship("Bot", back_populates="owner", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.email}>"


class Bot(Base):
    """Bot model"""

    __tablename__ = "bots"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    description = Column(String)
    instructions = Column(Text)  # System prompt for the bot
    is_active = Column(Boolean, default=True)
    embedding_model = Column(String, default="text-embedding-3-small")
    llm_model = Column(String, default="gpt-3.5-turbo")
    temperature = Column(Float, default=0.7)
    max_tokens = Column(Integer, default=500)
    vector_store_path = Column(String)  # Path to FAISS index
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    owner = relationship("User", back_populates="bots")
    documents = relationship("Document", back_populates="bot", cascade="all, delete-orphan")
    chat_histories = relationship("ChatHistory", back_populates="bot", cascade="all, delete-orphan")
    analytics = relationship("Analytics", back_populates="bot", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Bot {self.name}>"


class Document(Base):
    """Document model"""

    __tablename__ = "documents"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    bot_id = Column(String, ForeignKey("bots.id"), nullable=False, index=True)
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_type = Column(String)  # pdf, docx, txt, url
    file_size = Column(Integer)
    status = Column(String, default="pending")  # pending, processing, completed, failed
    total_chunks = Column(Integer, default=0)
    error_message = Column(String)
    metadata = Column(JSON)  # Additional metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    bot = relationship("Bot", back_populates="documents")

    def __repr__(self):
        return f"<Document {self.filename}>"


class ChatHistory(Base):
    """Chat history model"""

    __tablename__ = "chat_histories"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    bot_id = Column(String, ForeignKey("bots.id"), nullable=False, index=True)
    user_message = Column(Text, nullable=False)
    bot_response = Column(Text, nullable=False)
    sources = Column(JSON)  # List of source documents
    tokens_used = Column(Integer)
    processing_time = Column(Float)  # milliseconds
    rating = Column(Integer)  # 1-5 star rating
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    bot = relationship("Bot", back_populates="chat_histories")

    def __repr__(self):
        return f"<ChatHistory {self.id}>"


class Analytics(Base):
    """Analytics model"""

    __tablename__ = "analytics"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    bot_id = Column(String, ForeignKey("bots.id"), nullable=False, index=True)
    date = Column(DateTime, default=datetime.utcnow, index=True)
    total_queries = Column(Integer, default=0)
    successful_queries = Column(Integer, default=0)
    failed_queries = Column(Integer, default=0)
    avg_response_time = Column(Float)
    avg_rating = Column(Float)

    # Relationships
    bot = relationship("Bot", back_populates="analytics")

    def __repr__(self):
        return f"<Analytics {self.bot_id}>"