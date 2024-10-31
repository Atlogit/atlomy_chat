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
    
    # Author and work names
    author_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    work_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    
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

    def _get_abbreviated_author_name(self) -> str:
        """Get abbreviated author name (e.g., 'Galenus Med.' -> 'Gal.')."""
        if not self.author_name:
            return f"[{self.author_id_field}]"
        
        # Split author name and take first word
        parts = self.author_name.split()
        if not parts:
            return f"[{self.author_id_field}]"
            
        # Get first 3 letters of first word
        abbrev = parts[0][:3] + "."
        
        # Add designation if present (e.g., "Med.", "Phil.")
        if len(parts) > 1 and len(parts[-1]) <= 4:
            abbrev += f" {parts[-1]}"
            
        return abbrev

    def _get_abbreviated_work_name(self) -> str:
        """Get abbreviated work name."""
        if not self.work_name:
            return f"[{self.work_number_field}]"
            
        # Split work name into words
        words = self.work_name.split()
        if not words:
            return f"[{self.work_number_field}]"
            
        # Take first letter of each significant word
        abbrev = ""
        for word in words:
            # Skip common words like "de", "in", etc.
            if word.lower() in ["de", "in", "et", "ad", "the", "a", "an"]:
                continue
            if word:
                abbrev += word[0].upper()
                
        # If no abbreviation was created, use first 3 letters of first word
        if not abbrev and words:
            abbrev = words[0][:3].capitalize()
            
        return abbrev + "."
    
    def __repr__(self) -> str:
        citation_parts = []
        
        # Use author and work names if available, otherwise use ID fields
        if self.author_name:
            citation_parts.append(self.author_name)
        else:
            citation_parts.append(f"[{self.author_id_field}]")
            
        if self.work_name:
            citation_parts.append(self.work_name)
        else:
            citation_parts.append(f"[{self.work_number_field}]")
            
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
            f"citation={', '.join(citation_parts)}"
            + (f", {', '.join(structure_parts)}" if structure_parts else "")
            + ")"
        )

    def format_citation(self, abbreviated: bool = False) -> str:
        """Format a citation string.
        
        Args:
            abbreviated: If True, returns abbreviated format (e.g., "Gal. San. 6.135")
                       If False, returns full format (e.g., "Galenus Med., De sanitate tuenda libri vi, Volume 6: Chapter 135")
        """
        if abbreviated:
            # Get abbreviated author and work names
            author = self._get_abbreviated_author_name()
            work = self._get_abbreviated_work_name()
            
            # Start with author and work
            citation = f"{author} {work}"
            
            # Add location components with minimal formatting
            if self.volume:
                citation += f" {self.volume}"
            if self.chapter:
                citation += f".{self.chapter}"
            if self.line:
                citation += f".{self.line}"
            if self.section:
                citation += f".{self.section}"
                
            return citation.strip()
        else:
            # Use author and work names if available, otherwise use ID fields
            author = self.author_name or f"[{self.author_id_field}]"
            work = self.work_name or f"[{self.work_number_field}]"
            
            citation = f"{author}, {work}"
            
            # Add structural components if available
            components = []
            if self.volume:
                components.append(f"Volume {self.volume}")
            if self.chapter:
                components.append(f"Chapter {self.chapter}")
            if self.line:
                components.append(f"Line {self.line}")
            if self.section:
                components.append(f"Section {self.section}")
                
            if components:
                citation += f", {', '.join(components)}"
                
            return citation

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
