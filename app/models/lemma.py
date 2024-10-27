from typing import Optional, Dict, Any, List
from sqlalchemy import String, ARRAY, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from . import Base

class Lemma(Base):
    """Model for storing lemmatized words and their translations.
    
    This model represents the base forms of words (lemmas) across different
    languages, their categories, and translations. It serves as the foundation
    for lexical analysis and cross-language study.
    """
    __tablename__ = "lemmas"

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True)
    
    # Required fields
    lemma: Mapped[str] = mapped_column(
        String,
        nullable=False,
        comment="The base form (lemma) of the word"
    )
    
    # Optional fields
    language_code: Mapped[Optional[str]] = mapped_column(
        String(5),
        nullable=True,
        comment="ISO language code (e.g., 'grc' for ancient Greek)"
    )
    
    # Categories for the lemma
    categories: Mapped[List[str]] = mapped_column(
        ARRAY(String),
        nullable=False,
        default=list,
        comment="Categories or classifications for this lemma"
    )
    
    # Translations and additional metadata
    translations: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        default=dict,
        comment="Translations and additional linguistic metadata"
    )
    
    # Relationships
    analyses = relationship("LemmaAnalysis", back_populates="lemma", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"Lemma(id={self.id}, lemma={self.lemma}, lang={self.language_code}, categories={self.categories})"
