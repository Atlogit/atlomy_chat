from typing import Optional, Dict, Any
from sqlalchemy import String, ForeignKey, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from . import Base

class LemmaAnalysis(Base):
    """Model for storing LLM-generated analyses of lemmas.
    
    This model stores both the raw text analysis and structured data from
    AWS Bedrock (Claude-3) analysis of lemmas, including citations and
    references to support the analysis.
    """
    __tablename__ = "lemma_analyses"

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True)
    
    # Foreign key to Lemma
    lemma_id: Mapped[int] = mapped_column(
        ForeignKey("lemmas.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Analysis content
    analysis_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Full text of the LLM-generated analysis"
    )
    
    # Structured analysis data
    analysis_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        default=dict,
        comment="Structured data from the analysis (e.g., key findings, patterns)"
    )
    
    # Citations and references
    citations: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        default=dict,
        comment="Citations and references supporting the analysis"
    )
    
    # Attribution
    created_by: Mapped[str] = mapped_column(
        String,
        nullable=False,
        comment="Identifier for the creator of this analysis"
    )
    
    # Relationship
    lemma = relationship("Lemma", back_populates="analyses")
    
    def __repr__(self) -> str:
        return f"LemmaAnalysis(id={self.id}, lemma_id={self.lemma_id}, created_by={self.created_by})"