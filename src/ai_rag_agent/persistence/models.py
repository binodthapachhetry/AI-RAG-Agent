# src/ai_rag_agent/persistence/models.py
from __future__ import annotations

from datetime import datetime

from sqlalchemy import ForeignKey, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Document(Base):
    __tablename__ = "documents"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    uri: Mapped[str] = mapped_column(String(512), unique=True, index=True)  # where it came from
    content_hash: Mapped[str] = mapped_column(String(64), index=True)  # for change detection
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    chunks: Mapped[list[Chunk]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )


class Chunk(Base):
    __tablename__ = "chunks"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), index=True
    )
    text: Mapped[str] = mapped_column(Text)
    token_count: Mapped[int] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    document: Mapped[Document] = relationship(back_populates="chunks")


class QueryLog(Base):
    __tablename__ = "queries"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class AnswerLog(Base):
    __tablename__ = "answers"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    query_id: Mapped[int] = mapped_column(ForeignKey("queries.id", ondelete="CASCADE"), index=True)
    answer_json: Mapped[str] = mapped_column(Text)  # store JSON string for simplicity
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
