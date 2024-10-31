"""
Model for storing sentence data with references to source lines and NLP analysis.
"""

from typing import List, Dict, Any, Optional
from sqlalchemy import String, Integer, ForeignKey, JSON, ARRAY, Table, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship
from . import Base

# Association table for many-to-many relationship between sentences and text lines
sentence_text_lines = Table(
    'sentence_text_lines',
    Base.metadata,
    Column('sentence_id', Integer, ForeignKey('sentences.id', ondelete="CASCADE"), primary_key=True),
    Column('text_line_id', Integer, ForeignKey('text_lines.id', ondelete="CASCADE"), primary_key=True),
    Column('position_start', Integer, nullable=False),
    Column('position_end', Integer, nullable=False)
)

class Sentence(Base):
    """Model for storing sentences parsed from text lines.
    
    Each sentence maintains references to its source lines and can span
    multiple lines. The model also stores NLP analysis data at the
    sentence level. A sentence can span multiple lines, and a line can
    contain multiple sentences.
    """
    __tablename__ = "sentences"

    # Primary key as auto-incrementing integer
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )
    
    # The complete sentence text
    content: Mapped[str] = mapped_column(String, nullable=False)
    
    # References to source lines
    source_line_ids: Mapped[List[int]] = mapped_column(
        ARRAY(Integer),
        nullable=False,
        comment="IDs of TextLine objects that make up this sentence"
    )
    
    # Position information in source lines
    start_position: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Start position in first source line"
    )
    end_position: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="End position in last source line"
    )
    
    # NLP analysis data
    spacy_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="Complete spaCy analysis data for the sentence"
    )
    
    # Categories extracted from NLP analysis
    categories: Mapped[List[str]] = mapped_column(
        ARRAY(String),
        nullable=False,
        default=list,
        comment="Categories extracted from spaCy analysis"
    )
    
    # Many-to-many relationship with text lines
    text_lines = relationship(
        "TextLine",
        secondary=sentence_text_lines,
        back_populates="sentences",
        cascade="all, delete"
    )
    
    # One-to-many relationship with lexical values
    lexical_values = relationship("LexicalValue", back_populates="sentence")
    
    def __repr__(self) -> str:
        return f"Sentence(id={self.id}, content={self.content[:50]}...)"
