from datetime import datetime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncAttrs

class Base(AsyncAttrs, DeclarativeBase):
    """Base class for all database models.
    
    This base provides common functionality and timestamp columns for all models.
    AsyncAttrs enables async operations on model instances.
    """
    
    # Common columns that should be included in all tables
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

# Import all models here for Alembic to discover them
from .author import Author
from .text import Text
from .text_division import TextDivision
from .text_line import TextLine
from .lemma import Lemma
from .lemma_analysis import LemmaAnalysis
from .lexical_value import LexicalValue
from .sentence import Sentence

# List of all models for easy access
__all__ = [
    "Base",
    "Author",
    "Text",
    "TextDivision",
    "TextLine",
    "Lemma",
    "LemmaAnalysis",
    "LexicalValue",
    "Sentence"
]
