from typing import Optional, Dict, Any, List
from sqlalchemy import String, Integer, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models import Base

class TextLine(Base):
    """Model for storing individual lines of text with their NLP annotations.
    
    This model represents individual lines within text divisions, including
    the raw text content, categories, and associated spaCy NLP analysis data.
    Categories are stored as a separate field for efficient querying, while
    still maintaining the full NLP data in spacy_tokens.
    """
    __tablename__ = "text_lines"

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True)
    
    # Sentence ID for lexical value relationships
    sentence_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), unique=True, nullable=False)
    
    # Foreign key to TextDivision
    division_id: Mapped[int] = mapped_column(
        ForeignKey("text_divisions.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Line number within the division
    line_number: Mapped[int] = mapped_column(Integer, nullable=False)
    
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
    lexical_values = relationship("LexicalValue", back_populates="sentence")
    
    def __repr__(self) -> str:
        return f"TextLine(id={self.id}, division_id={self.division_id}, line={self.line_number}, categories={self.categories})"
