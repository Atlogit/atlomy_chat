"""Citation processing module for text migration.

This module handles the parsing and processing of citations and their components.
"""

import re
from typing import Dict, Optional, Tuple

class CitationProcessor:
    """Processes citations and their components."""

    def __init__(self):
        # Compile regex patterns
        self.section_pattern = re.compile(r'(\[\d*\]\s*\[\d*\](?:\s*\[\w*\]){0,2})')  # Allow empty brackets
        
        # Pattern to match various title formats:
        # .t.1, .847a.t., ..t., 6.1.t., 5.899.t1, .847a.t.
        self.title_pattern = re.compile(r'^(?:\.?(\w+)?\.)?(?:t\.?(\d*)|(\w+)\.t\.?)(?:\s+|$)(.*)')
        
        # Pattern for regular line numbers (non-title)
        self.line_pattern = re.compile(r'^\.?(\w+)?\.(\d+)\s*(.+)$')

    def extract_bracketed_values(self, citation: str) -> Dict[str, Optional[str]]:
        """Extract values from bracketed citation."""
        # Find all bracketed values
        brackets = re.findall(r'\[(\d*)\]', citation)
        values = {}
        
        # First bracket is author_id
        if len(brackets) >= 1 and brackets[0]:
            values['author_id'] = brackets[0]
            
        # Second bracket is work_id
        if len(brackets) >= 2 and brackets[1]:
            values['work_id'] = brackets[1]
            
        # Third bracket is division
        if len(brackets) >= 3 and brackets[2]:
            values['division'] = brackets[2]
            
        # Fourth bracket is subdivision
        if len(brackets) >= 4 and brackets[3]:
            values['subdivision'] = brackets[3]
            
        return values

    def extract_line_info(self, line: str) -> Tuple[str, bool, int, Optional[str]]:
        """Extract line number and content from a line.
        
        Returns:
            Tuple containing:
            - content (str): The actual text content
            - is_title (bool): Whether this is a title line
            - number (int): Line number or title number (negative for titles)
            - section (Optional[str]): Section identifier (e.g., '847a')
        """
        # First try to match title pattern
        title_match = self.title_pattern.match(line)
        if title_match:
            section, title_num, subsection, content = title_match.groups()
            
            # This is a title line
            if title_num:
                number = -int(title_num)  # Make title numbers negative
            else:
                number = 0  # For titles without numbers
                
            # Clean up content
            content = content.strip()
            if content.startswith('<') and content.endswith('>'):
                content = content[1:-1].strip()
            elif content.startswith('{') and content.endswith('}'):
                content = content[1:-1].strip()
                
            return content, True, number, section or subsection
            
        # Then try regular line pattern
        line_match = self.line_pattern.match(line)
        if line_match:
            section, line_num, content = line_match.groups()
            return content.strip(), False, int(line_num), section
            
        # If no patterns match, return the whole line as content
        return line.strip(), False, 0, None

    def split_sections(self, text: str) -> list:
        """Split text into sections based on citation patterns."""
        sections = self.section_pattern.split(text)
        if len(sections) < 2:
            raise ValueError("No sections found in the text")
        return sections
