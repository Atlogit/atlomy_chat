"""
Models for text lines, including both SQLAlchemy and Pydantic models.
"""

from typing import Optional, Dict, Any, List
from sqlalchemy import String, Integer, ForeignKey, JSON, Boolean
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pydantic import BaseModel
from app.models import Base
from app.models.sentence import sentence_text_lines

# Pydantic model for API responses
class TextLine(BaseModel):
    """
    API response model for text lines.
    
    Attributes:
        line_number: Sequential number of the line in the text
        content: The actual text content
        categories: Optional list of categories this line belongs to
        is_title: Whether this line is a title
        spacy_tokens: Optional spaCy NLP analysis data
    """
    line_number: int
    content: str
    categories: Optional[List[str]] = None
    is_title: Optional[bool] = False
    spacy_tokens: Optional[Dict[str, Any]] = None

# SQLAlchemy model for database
class TextLineDB(Base):
    """Model for storing individual lines of text with their NLP annotations.
    
    This model represents individual lines within text divisions, including
    the raw text content, categories, and associated spaCy NLP analysis data.
    Categories are stored as a separate field for efficient querying, while
    still maintaining the full NLP data in spacy_tokens.
    
    A text line can contain parts of multiple sentences, and a sentence
    can span multiple lines. This many-to-many relationship is managed
    through the sentence_text_lines association table.
    
    Lines can be either regular content or title lines, distinguished by
    the is_title flag. The line_number is used for both types.
    """
    __tablename__ = "text_lines"

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True)
    
    # Foreign key to TextDivision
    division_id: Mapped[int] = mapped_column(
        ForeignKey("text_divisions.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Line number within the division
    line_number: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Flag to indicate if this is a title line
    is_title: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    
    # Actual text content
    content: Mapped[str] = mapped_column(String, nullable=False)
    
    # Categories extracted from spaCy analysis
    # Stored separately for efficient querying
    categories: Mapped[List[str]] = mapped_column(
        ARRAY(String),
        nullable=False,
        default=list,
        comment="Categories extracted from spaCy analysis for efficient querying"
    )
    
    # Full spaCy NLP analysis data
    spacy_tokens: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        default=dict,
        comment="Complete spaCy token data including lemmas, POS tags, etc."
    )
    
    # Relationships
    division = relationship("TextDivision", back_populates="lines")
    sentences = relationship(
        "Sentence",
        secondary=sentence_text_lines,
        back_populates="text_lines",
        cascade="all, delete"
    )
    
    def __repr__(self) -> str:
        return f"TextLine(id={self.id}, division_id={self.division_id}, line={self.line_number}, is_title={self.is_title}, categories={self.categories})"
    
    def to_api_model(self) -> TextLine:
        """Convert to API response model."""
        return TextLine(
            line_number=self.line_number,
            content=self.content,
            categories=self.categories,
            is_title=self.is_title,
            spacy_tokens=self.spacy_tokens
        )
