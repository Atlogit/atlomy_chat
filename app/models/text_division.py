from typing import Optional, Dict, Any
from sqlalchemy import String, Integer, ForeignKey, JSON, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from . import Base

class TextDivision(Base):
    """Model for storing text divisions with both citation and structural components.
    
    Citation components:
    1. Author ID field (e.g., [0086])
    2. Work number field (e.g., [055])
    3. Abbreviation/epithet field (optional, e.g., [Divis])
    4. Fragment field (optional, e.g., [])
    
    Structural components:
    - Volume
    - Chapter
    - Line
    - Section (e.g., 847a)
    - Title information
    """
    __tablename__ = "text_divisions"

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True)
    
    # Foreign key to Text
    text_id: Mapped[int] = mapped_column(
        ForeignKey("texts.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Citation components
    author_id_field: Mapped[str] = mapped_column(String, nullable=False)
    work_number_field: Mapped[str] = mapped_column(String, nullable=False)
    epithet_field: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    fragment_field: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    
    # Structural components
    volume: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    chapter: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    line: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    section: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    
    # Title components
    is_title: Mapped[bool] = mapped_column(Boolean, default=False)
    title_number: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    title_text: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    
    # Additional metadata
    division_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        default=dict
    )
    
    # Relationships
    text = relationship("Text", back_populates="divisions")
    lines = relationship("TextLine", back_populates="division", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        citation_parts = [
            f"[{self.author_id_field}]",
            f"[{self.work_number_field}]"
        ]
        if self.epithet_field:
            citation_parts.append(f"[{self.epithet_field}]")
        if self.fragment_field:
            citation_parts.append(f"[{self.fragment_field}]")
            
        structure_parts = []
        if self.is_title:
            if self.section:
                structure_parts.append(f".{self.section}.t")
            else:
                structure_parts.append(".t")
            if self.title_number:
                structure_parts.append(f".{self.title_number}")
        else:
            if self.volume:
                structure_parts.append(f"Vol={self.volume}")
            if self.chapter:
                structure_parts.append(f"Ch={self.chapter}")
            if self.line:
                structure_parts.append(f"Lin={self.line}")
            if self.section:
                structure_parts.append(f"Sec={self.section}")
        
        return (
            f"TextDivision(id={self.id}, "
            f"citation={''.join(citation_parts)}"
            + (f", {', '.join(structure_parts)}" if structure_parts else "")
            + ")"
        )

    def from_citation(self, citation) -> None:
        """Update division fields from a Citation object."""
        if citation.author_id:
            self.author_id_field = citation.author_id
        if citation.work_id:
            self.work_number_field = citation.work_id
            
        # Handle title references
        if citation.title_number is not None:
            self.is_title = True
            self.title_number = citation.title_number
            if citation.section:
                self.section = citation.section
        else:
            self.is_title = False
            if citation.section:
                self.section = citation.section
            if citation.volume:
                self.volume = citation.volume
            if citation.chapter:
                self.chapter = citation.chapter
            if citation.line:
                self.line = citation.line
