"""
Citation parser for ancient text references.

This module contains the main CitationParser class that handles parsing citations
using work structures from TLG indexes.
"""

import re
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Any
import logging
from functools import wraps, lru_cache
from assets.indexes import tlg_index, work_numbers
from .citation_types import Citation
from .citation_utils import find_matching_work, map_level_to_field

# Use the same logger name as configured in corpus_base.py
logger = logging.getLogger('toolkit.parsers.citation_parser')

def log_exceptions(func):
    """Decorator to log exceptions raised by citation parsing functions."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.exception(f"Exception in {func.__name__}: {str(e)}")
            raise
    return wrapper

class CitationParser:
    """Parser for ancient text citations."""

    _instance = None
    
    # Default structure to use when no structure is found
    DEFAULT_STRUCTURE = ["Chapter", "Line"]
    
    @classmethod
    def get_instance(cls, config_path: Optional[Union[str, Path]] = None) -> 'CitationParser':
        """Get or create the singleton instance."""
        if cls._instance is None:
            cls._instance = cls(config_path)
            logger.info("Created new CitationParser instance")
        return cls._instance

    def __init__(self, config_path: Optional[Union[str, Path]] = None):
        """Initialize the citation parser."""
        # Prevent direct instantiation
        if CitationParser._instance is not None:
            raise RuntimeError("Use get_instance() to access CitationParser")
            
        self.config_path = config_path or Path(__file__).parent / "config" / "citation_config.json"
        self.config = self._load_config()
        self._structure_cache = {}
        self._pattern_cache = {}
        self.report = None  # Will be set by set_report
        logger.info("CitationParser initialized")

    def set_report(self, report: Any) -> None:
        """Set the pipeline report for tracking missing structures."""
        self.report = report

    @log_exceptions
    def _load_config(self) -> Dict:
        """Load citation configuration from JSON file."""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load citation config from {self.config_path}: {str(e)}")
            return {}

    def _analyze_citation_format(self, text: str) -> Tuple[int, Optional[str], Optional[str], Optional[str]]:
        """Analyze citation text to determine number of actual fields, title marker, and title content.
        Returns (num_fields, title_marker, line_number, title_content).
        """
        if not text.startswith('-Z'):
            return 0, None, None, None
            
        # Split by slashes and filter out empty parts
        parts = [p for p in text.split('/') if p and p != '-Z']
        
        # Look for title marker and content
        title_marker = None
        line_number = None
        title_content = None
        
        for i, part in enumerate(parts):
            # Check for title marker
            if part.startswith('t'):
                # Split on tab to separate marker from content
                marker_parts = part.split('\t', 1)  # Split on first tab only
                title_marker = marker_parts[0]  # Just the 't' or 't1' part
                
                # Look for title content after tab
                if len(marker_parts) > 1:
                    # Find opening curly brace after tab
                    content_start = marker_parts[1].find('{')
                    if content_start >= 0:
                        title_content = marker_parts[1][content_start + 1:]  # Include everything after {
                
                # If next part exists and current part is just 't', it's a line number
                if title_marker == 't' and i + 1 < len(parts):
                    line_number = parts[i + 1].split('\t')[0]
                    parts = parts[:i]
                else:
                    parts = parts[:i]
                break
                    
        return len(parts), title_marker, line_number, title_content

    def _extract_title_info(self, value: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """Extract title information from a value.
        Returns (is_title, title_number, actual_value).
        """
        if not value:
            return False, None, None
            
        # Check for bare 't' title marker
        if value == 't':
            return True, "1", None
            
        # Check for title marker (t1, t2, etc.)
        title_match = re.match(r't(\d+)', value)
        if title_match:
            title_num = title_match.group(1)
            return True, title_num, None
            
        # Check for title marker within value
        title_in_value = re.match(r'([^t]+)t(\d+)', value)
        if title_in_value:
            title_num = title_in_value.group(2)
            return True, title_num, title_in_value.group(1)
            
        return False, None, value

    def _get_citation_pattern(self, author_id: str, work_id: str) -> Optional[Dict]:
        """Get or create citation pattern based on work structure."""
        cache_key = f"{author_id}.{work_id}"
        if cache_key in self._pattern_cache:
            return self._pattern_cache[cache_key]
            
        # Get work structure - will now always return a structure
        structure = self.get_work_structure(author_id, work_id)
        logger.debug(f"Got work structure: {structure}")
        
        # Create pattern based on structure
        pattern_parts = []
        
        # Start with -Z and handle empty fields at start
        pattern_parts.append(r"-Z/+")  # Match -Z followed by one or more slashes
        
        # Add capture groups for actual fields in citation
        field_pattern = r"([^/]+?)(?=\t|\s*{|/|$)"  # Match field content up to tab, title content, slash, or end
        separator = r"/"
        
        # Add capture groups for all possible fields
        pattern_parts.append(field_pattern)  # First field
        pattern_parts.append(separator)
        pattern_parts.append(field_pattern)  # Second field
        pattern_parts.append(f"(?:{separator}{field_pattern})*")  # Additional fields
        
        # Add end anchor
        pattern = "^" + "".join(pattern_parts)
        
        logger.debug(f"Created pattern: {pattern}")
        logger.debug(f"Structure: {structure}")
        
        citation_pattern = {
            "regex": re.compile(pattern),
            "structure": structure,
            "pattern_parts": pattern_parts
        }
        
        self._pattern_cache[cache_key] = citation_pattern
        return citation_pattern

    @lru_cache(maxsize=1000)
    def get_work_structure(self, author_id: str, work_id: str) -> List[str]:
        """Get work structure using work_numbers and tlg_index with caching.
        Always returns a structure - uses default if none found."""
        cache_key = f"{author_id}.{work_id}"
        if cache_key in self._structure_cache:
            return self._structure_cache[cache_key]

        try:
            # Remove TLG prefix if present
            if author_id.startswith('TLG'):
                author_id = author_id[3:]

            # Get work name from works index
            author_works = work_numbers.TLG_WORKS_INDEX.get(author_id, {})
            if not author_works:
                logger.warning("Author %s not found in TLG_WORKS_INDEX, using default structure", author_id)
                if self.report:
                    self.report.add_missing_structure(author_id, work_id, "Unknown Work")
                return self.DEFAULT_STRUCTURE

            work_name = author_works.get(work_id)
            if not work_name:
                logger.warning("Work %s not found for author %s, using default structure", work_id, author_id)
                if self.report:
                    self.report.add_missing_structure(author_id, work_id, "Unknown Work")
                return self.DEFAULT_STRUCTURE

            # Find author entry in master index
            author_entry = next(
                (entry for entry in tlg_index.TLG_MASTER_INDEX.values() 
                 if entry.get("tlg_id") == f"TLG{author_id}"),
                None
            )
            if not author_entry:
                logger.warning("Author %s not found in TLG_MASTER_INDEX, using default structure", author_id)
                if self.report:
                    self.report.add_missing_structure(author_id, work_id, work_name)
                return self.DEFAULT_STRUCTURE

            # Find matching work structure
            structure = find_matching_work(work_name, author_entry.get("works", {}))
            if structure:
                self._structure_cache[cache_key] = structure
                return structure

            # Report missing structure if we have a report object
            if self.report:
                self.report.add_missing_structure(author_id, work_id, work_name)

            logger.warning(f"No structure found for work {author_id}.{work_id} ({work_name}), using default structure")
            return self.DEFAULT_STRUCTURE

        except Exception as e:
            logger.warning(f"Error finding work structure: {str(e)}, using default structure")
            if self.report:
                self.report.add_missing_structure(author_id, work_id, "Error Finding Work")
            return self.DEFAULT_STRUCTURE

    def parse_citation(self, text: str, author_id: Optional[str] = None, work_id: Optional[str] = None) -> Tuple[str, List[Citation]]:
        """Parse citations from text and return remaining text and citation objects."""
        if not text:
            return text, []

        # Get work-specific pattern for all citations
        if author_id and work_id:
            pattern = self._get_citation_pattern(author_id, work_id)
            if pattern:
                # Try to match and debug the result
                match = pattern["regex"].match(text)
                if match:
                    citation = Citation(
                        author_id=author_id,
                        work_id=work_id,
                        raw_citation=match.group(0).strip()
                    )
                    
                    # Set hierarchy levels based on structure
                    citation.hierarchy_levels = {}
                    
                    # Get the structure match groups
                    groups = match.groups()
                    logger.debug(f"Matched groups: {groups}")
                    
                    # Analyze actual citation format and get title info
                    num_fields, title_marker, line_number, title_content = self._analyze_citation_format(text)
                    logger.debug(f"Citation has {num_fields} fields, title marker: {title_marker}, line number: {line_number}")
                    
                    # Map groups to hierarchy levels and check for title markers
                    is_title = False
                    title_number = None
                    
                    # Only process the number of fields actually present in citation
                    for i, (level_name, value) in enumerate(zip(pattern["structure"], groups)):
                        if i >= num_fields:
                            break
                            
                        if not value:
                            continue
                            
                        level_key = level_name.lower()
                        logger.debug(f"Processing level {level_key} with value {value}")
                        
                        # Check for title marker
                        is_title_value, title_num, actual_value = self._extract_title_info(value)
                        if is_title_value:
                            is_title = True
                            # Only update title_number if we have one (preserve None for bare 't')
                            if title_num:
                                title_number = title_num
                            if actual_value:
                                value = actual_value
                            else:
                                logger.debug(f"Skipping value {value} as it's a title marker")
                                continue
                        
                        # Map the level name to a database field
                        field_name = map_level_to_field(level_key, pattern["structure"])
                        logger.debug(f"Mapped {level_key} to database field {field_name}")
                        
                        # Store the value using the mapped field name
                        citation.hierarchy_levels[field_name] = value
                        logger.debug(f"Set {field_name} = {value} in hierarchy_levels")
                        
                        # Set field attribute
                        if hasattr(citation, field_name):
                            setattr(citation, field_name, value)
                            logger.debug(f"Set {field_name} = {value} as attribute")
                    
                    # Set title flags if we found a title marker
                    if is_title or title_marker:
                        citation.is_title = True
                        citation.title_text = title_content  # Store raw title content
                        
                        if title_number:
                            # Clean title number to remove tab content
                            clean_title = title_number.split('\t')[0] if '\t' in title_number else title_number
                            citation.title_number = clean_title
                            # Also set line number for titles
                            citation.hierarchy_levels['line'] = clean_title
                        elif line_number:
                            # Clean line number to remove tab content
                            clean_line = line_number.split('\t')[0] if '\t' in line_number else line_number
                            citation.title_number = clean_line
                            # Also set line number for titles
                            citation.hierarchy_levels['line'] = clean_line
                        elif title_marker and len(title_marker) > 1:
                            # Extract just the number from t1, t2 etc
                            title_match = re.match(r't(\d+)', title_marker)
                            if title_match:
                                title_num = title_match.group(1)
                                citation.title_number = title_num
                                # Also set line number for titles
                                citation.hierarchy_levels['line'] = title_num
                            else:
                                title_num = title_marker[1:]
                                citation.title_number = title_num
                                # Also set line number for titles
                                citation.hierarchy_levels['line'] = title_num
                        else:
                            # For bare 't' marker with no number
                            citation.title_number = "1"
                            citation.hierarchy_levels['line'] = "1"

                    remaining = text[match.end():].strip()
                    logger.debug(f"Parsed citation: '{text}' -> groups {groups}")
                    logger.debug(f"Final hierarchy levels: {citation.hierarchy_levels}")
                    return remaining, [citation]
                else:
                    # Debug why the pattern didn't match
                    logger.debug(f"Pattern did not match. Text: '{text}'")
                    logger.debug(f"Pattern: '{pattern['regex'].pattern}'")
                    # Try to match without the end anchor to see if that's the issue
                    test_pattern = re.compile("^" + "".join(pattern["pattern_parts"]))
                    test_match = test_pattern.match(text)
                    
        return text, []

    def reset(self):
        """Reset parser state."""
        self._structure_cache.clear()
        self._pattern_cache.clear()
        self.report = None
        logger.debug("Reset CitationParser state")
