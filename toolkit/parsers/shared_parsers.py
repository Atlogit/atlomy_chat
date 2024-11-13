"""
Singleton class for shared parser components.

Provides centralized access to shared parser utilities and resources.
"""

import logging
from typing import Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class SharedParsers:
    """Singleton class for shared parser components."""
    
    _instance = None
    _sentence_utils = None
    _citation_parser = None
    
    @classmethod
    def get_instance(cls, config_path: Optional[Path] = None) -> 'SharedParsers':
        """Get or create the singleton instance."""
        if cls._instance is None:
            cls._instance = cls(config_path)
            logger.info("Created new SharedParsers instance")
        return cls._instance
    
    def __init__(self, config_path: Optional[Path] = None):
        """Initialize shared parser components."""
        # Prevent direct instantiation
        if SharedParsers._instance is not None:
            raise RuntimeError("Use get_instance() to access SharedParsers")
            
        self._config_path = config_path
        logger.info("Initialized shared parser components")
    
    @property
    def sentence_utils(self):
        """Lazy initialization of SentenceUtils."""
        if self._sentence_utils is None:
            from .sentence_utils import SentenceUtils
            self._sentence_utils = SentenceUtils.get_instance()
        return self._sentence_utils
    
    @property
    def citation_parser(self):
        """Lazy initialization of CitationParser."""
        if self._citation_parser is None:
            from .citation import CitationParser
            self._citation_parser = CitationParser.get_instance(self._config_path)
        return self._citation_parser
    
    def reset(self):
        """Reset stateful components."""
        if self._citation_parser:
            self._citation_parser.reset()
        logger.debug("Reset SharedParsers state")
