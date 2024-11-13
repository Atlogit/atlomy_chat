"""
Citation types and patterns for ancient text references.

This module contains the Citation dataclass and level patterns used for parsing
citations in ancient texts.
"""

from dataclasses import dataclass, field
from typing import Dict, Optional

# Mapping of level patterns to database fields using regex
LEVEL_PATTERNS = {
    'volume': r'.*vol.*',  # Matches if 'vol' appears anywhere in the string
    'page': r'.*pag.*',    # Matches if 'pag' appears anywhere in the string
    'section': r'.*sec.*',  # Matches if 'sec' appears anywhere in the string
    'chapter': r'.*cha.*',  # Matches if 'cha' appears anywhere in the string
    'play': r'.*pla.*',    # Matches if 'pla' appears anywhere in the string
    'line': r'.*lin.*',    # Matches if 'lin' appears anywhere in the string
    'fragment': r'.*fra.*', # Matches if 'fra' appears anywhere in the string
    'book': r'.*boo.*'     # Matches if 'boo' appears anywhere in the string
}

@dataclass
class Citation:
    """Container for citation information."""
    # TLG Reference components
    author_id: Optional[str] = None
    work_id: Optional[str] = None
    hierarchy_levels: Dict[str, Optional[str]] = None
    division: Optional[str] = None
    subdivision: Optional[str] = None
    
    # Volume/Book/Chapter/Line components
    volume: Optional[str] = None
    book: Optional[str] = None
    chapter: Optional[str] = None
    line: Optional[str] = None
    
    # Section components
    section: Optional[str] = None
    subsection: Optional[str] = None
    
    # Page component
    page: Optional[str] = None
    
    # Fragment component
    fragment: Optional[str] = None
    
    # Title components
    title_number: Optional[str] = None    # Number from t1, t2, etc.
    title_text: Optional[str] = None      # Complete title text (joined from parts if multiline)
    title_parts: Dict[str, str] = field(default_factory=dict)  # Store parts for multiline titles
    is_title: bool = False                # Flag for title citations
    
    # Original citation text
    raw_citation: str = ""

    def __post_init__(self):
        """Initialize hierarchy_levels if not provided."""
        self.hierarchy_levels = self.hierarchy_levels or {}
        self.title_parts = self.title_parts or {}
        
        # If we have title_text but no parts, store it as first part
        if self.title_text and not self.title_parts:
            self.title_parts["1"] = self.title_text

    def __str__(self) -> str:
        """Format citation as string."""
        # If raw_citation is present, use it
        if self.raw_citation:
            return self.raw_citation
            
        # Handle title citations
        if self.is_title:
            # Case 1: -Z//page/t2 {content}
            if self.page:
                citation = f"-Z//{self.page}/t"
                if self.title_number and self.title_number != "1":
                    citation += self.title_number
            # Case 2: -Z//t/1 {content}
            else:
                citation = f"-Z//t/{self.title_number or '1'}"
                
            # Add title content if available
            if self.get_complete_title():
                citation += f"\t{{{self.get_complete_title()}}}"
            return citation
            
        # Handle regular citations
        if self.hierarchy_levels:
            values = []
            # Add empty fields on left
            empty_fields = 4 - len(self.hierarchy_levels)
            for _ in range(empty_fields):
                values.append('')
            # Add values in order
            for key, value in sorted(self.hierarchy_levels.items()):
                values.append(value if value else '')
            # Join with forward slashes
            return f"-Z/{'/'.join(values)}"
            
        return ""

    def format_with_context(self) -> str:
        """Format citation including author/work context."""
        parts = []
        
        # Add TLG reference if present
        if self.author_id and self.work_id:
            parts.append(f"[{self.author_id}][{self.work_id}]")
            if self.division:
                parts.append(f"[{self.division}]")
            if self.subdivision:
                parts.append(f"[{self.subdivision}]")
        
        # Add the basic citation
        basic_citation = str(self)
        if basic_citation:
            parts.append(basic_citation)
            
        return ''.join(parts)

    def get_complete_title(self) -> Optional[str]:
        """Get complete title by joining parts in order.
        
        Returns:
            The complete title if all parts are available, None otherwise
        """
        if not self.title_parts:
            return self.title_text if self.title_text else None
            
        # Join parts in numerical order
        ordered_parts = []
        for num in sorted(self.title_parts.keys(), key=lambda x: int(x)):
            ordered_parts.append(self.title_parts[num])
            
        complete_title = ' '.join(ordered_parts)
        self.title_text = complete_title  # Store joined title
        return complete_title

    def add_title_part(self, part: str, number: Optional[str] = None) -> None:
        """Add a part to a multiline title.
        
        Args:
            part: The title text to add
            number: Optional part number, defaults to next available
        """
        if not number:
            # Get next number if not provided
            existing_numbers = [int(n) for n in self.title_parts.keys()]
            number = str(max(existing_numbers) + 1 if existing_numbers else 1)
            
        self.title_parts[number] = part
        # Update complete title
        self.title_text = self.get_complete_title()
