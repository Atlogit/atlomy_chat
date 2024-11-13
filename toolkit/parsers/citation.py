"""
Citation parsing and formatting for ancient text references.

This module provides the main interface for citation parsing functionality.
Implementation details are split across multiple modules for maintainability:

- citation_types.py: Contains Citation dataclass and level patterns
- citation_utils.py: Utility functions for work name matching
- citation_parser.py: Core CitationParser implementation
"""

from .citation_types import Citation, LEVEL_PATTERNS
from .citation_utils import (
    map_level_to_field,
    normalize_work_name,
    find_matching_work
)
from .citation_parser import CitationParser

__all__ = [
    'Citation',
    'CitationParser',
    'LEVEL_PATTERNS',
    'map_level_to_field',
    'normalize_work_name',
    'find_matching_work'
]
