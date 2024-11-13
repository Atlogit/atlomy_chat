"""
Utility functions for citation parsing and work name matching.

This module contains helper functions for normalizing work names and finding
matching work structures in the TLG indexes.
"""

import regex as re
import logging
import unicodedata
from typing import Dict, List, Optional, Any, Union

# Use the same logger name as configured in corpus_base.py
logger = logging.getLogger('toolkit.parsers.citation_utils')

def map_level_to_field(level_name: str, work_structure: Optional[List[str]] = None) -> str:
    """Map a level name to its corresponding database field using regex patterns.
    Always returns a valid field name, defaulting to 'chapter' if no mapping found."""
    from .citation_types import LEVEL_PATTERNS
    
    # Convert to lowercase and strip whitespace
    normalized = level_name.lower().strip()
    logger.debug(f"Mapping level '{level_name}' with structure {work_structure}")
    
    # Try direct mapping first for precise matches
    direct_mappings = {
        'book': 'book',
        'chapter': 'chapter',
        'section': 'section',
        'line': 'line',
        'volume': 'volume',
        'fragment': 'fragment',
        'page': 'page'
    }
    
    if normalized in direct_mappings:
        mapped = direct_mappings[normalized]
        logger.debug(f"Direct mapping: {normalized} -> {mapped}")
        return mapped
    
    # If no direct match, try pattern matching
    for field, pattern in LEVEL_PATTERNS.items():
        if re.search(pattern, normalized, re.IGNORECASE):
            logger.debug(f"Pattern match: {normalized} -> {field}")
            return field
    
    # If we have a work structure, try to map based on structure
    if work_structure:
        structure_levels = [level.lower() for level in work_structure]
        
        # Special cases based on structure
        if 'play' in structure_levels:
            logger.debug("Found 'play' in structure, mapping to chapter")
            return 'chapter'  # Map 'play' to chapter
        if 'book' in structure_levels:
            logger.debug("Found 'book' in structure, using book")
            return 'book'     # Prefer 'book' if in structure
        
        # Try each pattern with structure context
        for level in structure_levels:
            for field, pattern in LEVEL_PATTERNS.items():
                if re.search(pattern, level, re.IGNORECASE):
                    logger.debug(f"Pattern match with structure context: {level} -> {field}")
                    return field
                    
        # If structure has a valid field, use the first one
        for level in structure_levels:
            if level in direct_mappings:
                mapped = direct_mappings[level]
                logger.debug(f"Using first valid field from structure: {level} -> {mapped}")
                return mapped
    
    # Default to chapter if no mapping found
    logger.debug(f"No mapping found for level '{level_name}', defaulting to chapter")
    return 'chapter'

def normalize_work_name(name: str) -> str:
    """Normalize work name for comparison.
    
    Handles:
    1. Special characters (+$%)
    2. Square brackets and their content [Sp.]
    3. Parentheses and their content (...)
    4. Extra whitespace
    5. Leading numbers
    """
    if not name:
        return ""
    
    # Remove leading numbers and dots
    normalized = re.sub(r'^\d+\.?\s*', '', name)
    # Remove special characters
    normalized = re.sub(r'[+$%]', '', normalized)
    # Remove content in square brackets
    normalized = re.sub(r'\s*\[[^\]]*\]', '', normalized)
    # Remove content in parentheses
    normalized = re.sub(r'\s*\([^)]*\)?', '', normalized)
    # Normalize whitespace and convert to lowercase
    return ' '.join(normalized.lower().split())

def create_fuzzy_pattern(text: str, max_errors: int = 3) -> str:
    """Create a fuzzy matching pattern that's tolerant of minor differences.
    
    Args:
        text: The text to create a pattern for
        max_errors: Maximum number of allowed differences
        
    Returns:
        A regex pattern string that can be used for fuzzy matching
    """
    if not text:
        return ""
        
    # Normalize the text
    decomposed = unicodedata.normalize('NFKD', text.lower())
    
    # Build pattern parts
    pattern_parts = []
    for char in decomposed:
        if unicodedata.category(char).startswith('P'):  # Punctuation
            pattern_parts.append(r'\s*')  # Make punctuation optional and allow whitespace
        elif char.isspace():
            pattern_parts.append(r'\s+')  # Require at least one whitespace
        else:
            # For regular characters, make them case-insensitive and allow for variations
            pattern_parts.append(f'[{char.upper()}{char.lower()}]')
            
    # Join parts and allow for fuzzy matching
    pattern = r'\s*'.join(''.join(pattern_parts).split())
    
    # Add word boundaries and make the whole pattern fuzzy
    return f"(?:{pattern}){{e<={max_errors}}}"

def find_matching_work(work_name: str, works_dict: Dict[str, Any]) -> Optional[List[str]]:
    """Find matching work structure using fuzzy name matching.
    
    First tries exact matching, then falls back to fuzzy matching if no exact match is found.
    """
    if not work_name:
        return None
        
    normalized_name = normalize_work_name(work_name)
    logger.debug(f"Looking for work with normalized name: '{normalized_name}'")
    
    # Try to find exact match
    for key, value in works_dict.items():
        # Get the name to check against
        if not key and isinstance(value, list) and value:
            name_to_check = normalize_work_name(value[0])
            structure = value  # Don't slice, use whole list
        else:
            name_to_check = normalize_work_name(key)
            structure = value  # Don't slice, use whole list
            
        # Skip empty names
        if not name_to_check:
            continue
            
        # Try exact match first
        if normalized_name == name_to_check:
            logger.debug(f"Found exact match: '{key}' -> {structure}")
            return structure
            
    # If no exact match found, try fuzzy matching
    fuzzy_pattern = create_fuzzy_pattern(normalized_name)
    best_match = None
    best_match_structure = None
    best_match_ratio = 0
    
    for key, value in works_dict.items():
        # Get the name to check against
        if not key and isinstance(value, list) and value:
            name_to_check = normalize_work_name(value[0])
            structure = value  # Don't slice, use whole list
            logger.debug(f"Checking array value for fuzzy match: '{value[0]}' -> '{name_to_check}'")
        else:
            name_to_check = normalize_work_name(key)
            structure = value  # Don't slice, use whole list
            logger.debug(f"Checking key for fuzzy match: '{key}' -> '{name_to_check}'")
            
        # Skip empty names
        if not name_to_check:
            continue
            
        # Try fuzzy match
        try:
            if re.search(fuzzy_pattern, name_to_check, re.IGNORECASE):
                # Calculate match ratio based on length difference
                ratio = len(name_to_check) / len(normalized_name)
                if 0.8 <= ratio <= 1.2:  # Allow 20% length difference
                    if best_match is None or abs(1 - ratio) < abs(1 - best_match_ratio):
                        best_match = name_to_check
                        best_match_structure = structure
                        best_match_ratio = ratio
                        logger.debug(f"New best fuzzy match: '{best_match}' (ratio: {best_match_ratio})")
        except re.error:
            logger.warning(f"Invalid regex pattern for fuzzy matching: {fuzzy_pattern}")
            continue
            
    if best_match:
        logger.debug(f"Found fuzzy match: '{best_match}' -> {best_match_structure}")
        return best_match_structure
            
    logger.debug(f"No match found for '{work_name}'")
    return None
