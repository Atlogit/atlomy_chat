from typing import Optional, Dict, Any
from sqlalchemy import String, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from . import Base

class Text(Base):
    """Model for storing ancient medical texts.
    
    This model represents the main text documents, linking them to authors
    and storing metadata in a flexible JSONB field.
    """
    __tablename__ = "texts"

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True)
    
    # Foreign key to Author
    author_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("authors.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # Required fields
    title: Mapped[str] = mapped_column(String, nullable=False)
    
    # Optional fields
    reference_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    text_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        default=dict
    )
    
    # Relationships
    author = relationship("Author", back_populates="texts")
    divisions = relationship("TextDivision", back_populates="text", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"Text(id={self.id}, title={self.title}, ref={self.reference_code})"
