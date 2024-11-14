"""
Models for text divisions and responses.
"""

from typing import Optional, Dict, Any, List
from sqlalchemy import String, Integer, ForeignKey, JSON, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pydantic import BaseModel
from . import Base
from toolkit.parsers.citation import CitationParser
from .text_line import TextLine, TextLineAPI

# Pydantic models for API responses
class TextDivisionResponse(BaseModel):
    """API response model for text divisions."""
    id: str
    author_name: Optional[str] = None
    work_name: Optional[str] = None
    volume: Optional[str] = None
    chapter: Optional[str] = None
    section: Optional[str] = None
    is_title: bool
    title_number: Optional[str] = None
    title_text: Optional[str] = None
    metadata: Optional[Dict] = None
    lines: Optional[List[TextLineAPI]] = None

class TextResponse(BaseModel):
    """API response model for complete texts."""
    id: str
    title: str
    work_name: Optional[str] = None
    author: Optional[str] = None
    reference_code: Optional[str] = None
    metadata: Optional[Dict] = None
    divisions: Optional[List[TextDivisionResponse]] = None

# SQLAlchemy model for database
class TextDivision(Base):
    """Model for storing text divisions with both citation and structural components."""
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
    work_abbreviation_field: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    author_abbreviation_field: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    
    # Author and work names
    author_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    work_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    
    # Structural components
    fragment: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    volume: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    book: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # Added book field
    chapter: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    section: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    page: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    line: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    
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
        # First try to use author_name from database
        if self.author_name:
            parts = self.author_name.split()
            if parts:
                # Get first 3 letters of first word
                abbrev = parts[0][:3] + "."
                
                # Add designation if present (e.g., "Med.", "Phil.")
                if len(parts) > 1 and len(parts[-1]) <= 4:
                    abbrev += f" {parts[-1]}"
                    
                return abbrev
            
        # If no author_name, try to get it from text relationship
        if self.text and self.text.author and self.text.author.name:
            parts = self.text.author.name.split()
            if parts:
                abbrev = parts[0][:3] + "."
                if len(parts) > 1 and len(parts[-1]) <= 4:
                    abbrev += f" {parts[-1]}"
                return abbrev
                
        # Fallback to ID field
        return self.author_id_field

    def _get_abbreviated_work_name(self) -> str:
        """Get abbreviated work name."""
        # First try work_name from database
        work_name = self.work_name
        
        # If no work_name, try to get it from text relationship
        if not work_name and self.text:
            work_name = self.text.title
            
        if not work_name:
            return self.work_number_field
            
        # Split work name into words
        words = work_name.split()
        if not words:
            return self.work_number_field
            
        # Take first letter of each significant word
        abbrev = ""
        for word in words:
            # Skip common words like "de", "in", etc.
            if word.lower() not in ["de", "in", "et", "ad", "the", "a", "an"]:
                if word:
                    abbrev += word[0].upper()
                
        # If no abbreviation was created, use first 3 letters of first word
        if not abbrev and words:
            abbrev = words[0][:3].capitalize()
            
        return abbrev + "."

    def _get_work_structure(self) -> Optional[List[str]]:
        """Get work structure from citation parser."""
        if self.author_id_field and self.work_number_field:
            parser = CitationParser.get_instance()
            return parser.get_work_structure(self.author_id_field, self.work_number_field)
        return None

    def _get_location_components(self, structure: Optional[List[str]] = None) -> List[str]:
        """Get location components in the correct order based on work structure."""
        components = []
        
        # If we have a work structure, use it to order the components
        if structure:
            structure_levels = [level.lower() for level in structure]
            field_map = {
                'fragment': ('fragment', 'Fragment'),
                'volume': ('volume', 'Volume'),
                'book': ('book', 'Book'),  # Added book mapping
                'page': ('page', 'Page'),
                'chapter': ('chapter', 'Chapter'),
                'section': ('section', 'Section'),
                'line': ('line', 'Line')
            }
            
            # Add components in structure order
            for level in structure_levels:
                for field_key, (attr, label) in field_map.items():
                    if level == field_key and getattr(self, attr):
                        components.append(f"{label} {getattr(self, attr)}")
                        break
        else:
            # Fallback to default order if no structure
            if self.fragment:
                components.append(f"Fragment {self.fragment}")
            if self.volume:
                components.append(f"Volume {self.volume}")
            if self.book:  # Added book component
                components.append(f"Book {self.book}")
            if self.chapter:
                components.append(f"Chapter {self.chapter}")
            if self.page:
                components.append(f"Page {self.page}")
            if self.section:
                components.append(f"Section {self.section}")
            if self.line:
                components.append(f"Line {self.line}")
                
        return components
    
    def __repr__(self) -> str:
        citation_parts = []
        
        # Use author and work names if available, otherwise use ID fields
        if self.author_name:
            citation_parts.append(self.author_name)
        else:
            citation_parts.append(self.author_id_field)
            
        if self.work_name:
            citation_parts.append(self.work_name)
        else:
            citation_parts.append(self.work_number_field)
            
        if self.work_abbreviation_field:
            citation_parts.append(f"[{self.work_abbreviation_field}]")
        if self.author_abbreviation_field:
            citation_parts.append(f"[{self.author_abbreviation_field}]")
            
        # Get work structure for ordering components
        structure = self._get_work_structure()
        components = self._get_location_components(structure)
        
        if components:
            citation_parts.append(f"({', '.join(components)})")
        
        return f"TextDivision(id={self.id}, citation={', '.join(citation_parts)})"

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
            
            # Get work structure for ordering components
            structure = self._get_work_structure()
            
            # Add location components in structure order
            if structure:
                structure_levels = [level.lower() for level in structure]
                field_map = {
                    'fragment': self.fragment,
                    'volume': self.volume,
                    'book': self.book,  # Added book field
                    'page': self.page,
                    'chapter': self.chapter,
                    'section': self.section,
                    'line': self.line
                }
                
                # Add components in structure order
                for level in structure_levels:
                    if level in field_map and field_map[level]:
                        citation += f".{field_map[level]}"
            else:
                # Fallback to default order if no structure
                if self.fragment:
                    citation += f".{self.fragment}"
                if self.volume:
                    citation += f".{self.volume}"
                if self.book:  # Added book field
                    citation += f".{self.book}"
                if self.chapter:
                    citation += f".{self.chapter}"
                if self.page:
                    citation += f".{self.page}"
                if self.section:
                    citation += f".{self.section}"
                if self.line:
                    citation += f".{self.line}"
                
            return citation.strip()
        else:
            # Try to get author name in this order:
            # 1. From author_name field
            # 2. From text -> author relationship
            # 3. Fallback to author_id_field
            author = (
                self.author_name or 
                (self.text.author.name if self.text and self.text.author else None) or 
                self.author_id_field
            )
            
            # Try to get work name in this order:
            # 1. From work_name field
            # 2. From text title
            # 3. Fallback to work_number_field
            work = (
                self.work_name or 
                (self.text.title if self.text else None) or 
                self.work_number_field
            )
            
            citation = f"{author}, {work}"
            
            # Get work structure for ordering components
            structure = self._get_work_structure()
            components = self._get_location_components(structure)
            
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
            if citation.fragment:
                self.fragment = citation.fragment
            if citation.section:
                self.section = citation.section
            if citation.volume:
                self.volume = citation.volume
            if citation.book:  # Added book field
                self.book = citation.book
            if citation.chapter:
                self.chapter = citation.chapter
            if citation.page:
                self.page = citation.page
            if citation.line:
                self.line = citation.line
                self.line = citation.line
