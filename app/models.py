from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, ForeignKey, Table
)
from sqlalchemy.orm import relationship
from app.database import Base


# Many-to-many: items <-> tags
item_tags = Table(
    "item_tags",
    Base.metadata,
    Column("item_id", Integer, ForeignKey("items.id"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id"), primary_key=True),
)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    items = relationship("Item", back_populates="owner")
    notes = relationship("Note", back_populates="author")


class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    source_type = Column(String, nullable=False)  # link | screenshot | pdf | text
    source_url = Column(String, nullable=True)
    original_file_path = Column(String, nullable=True)
    raw_text = Column(Text, default="")
    extracted_text = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)

    owner = relationship("User", back_populates="items")
    summary = relationship("Summary", back_populates="item", uselist=False, cascade="all, delete-orphan")
    tags = relationship("Tag", secondary=item_tags, back_populates="items")
    notes = relationship("Note", back_populates="item", cascade="all, delete-orphan")


class Summary(Base):
    __tablename__ = "summaries"

    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, ForeignKey("items.id"), nullable=False, unique=True)
    claim = Column(String, default="")
    bullet_summary = Column(Text, default="[]")   # JSON list
    detailed_explanation = Column(Text, default="")
    eli5_explanation = Column(Text, default="")
    limitations = Column(Text, default="")
    model_used = Column(String, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    item = relationship("Item", back_populates="summary")


class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True)

    items = relationship("Item", secondary=item_tags, back_populates="tags")


class Note(Base):
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, ForeignKey("items.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    note_text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    item = relationship("Item", back_populates="notes")
    author = relationship("User", back_populates="notes")
