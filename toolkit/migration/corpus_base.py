"""
Base class for corpus processing.

Provides initialization and common utilities for corpus processing.
"""

import os
import logging
from typing import Optional, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from .shared_components import SharedComponents

# Import migration logging configuration
from toolkit.migration.logging_config import get_migration_logger

# Use migration logger
logger = get_migration_logger('migration.corpus_base')

# Create logs directory if it doesn't exist
os.makedirs('logs', exist_ok=True)

class CorpusBase:
    """Base class for corpus processing components."""

    def __init__(self, 
                 session: AsyncSession, 
                 model_path: Optional[str] = None,
                 use_gpu: Optional[bool] = None):
        """Initialize the corpus processor.
        
        Args:
            session: SQLAlchemy async session
            model_path: Optional path to spaCy model
            use_gpu: Whether to use GPU for NLP processing (None for auto-detect)
        """
        # Get shared components instance
        self.shared = SharedComponents.get_instance(session, model_path, use_gpu)
        
        # For convenience, provide direct access to commonly used components
        self.session = self.shared.session
        self.sentence_parser = self.shared.sentence_parser
        self.citation_parser = self.shared.citation_parser
        self.nlp_pipeline = self.shared.nlp_pipeline
        
        logger.info("CorpusBase initialized with model_path=%s, use_gpu=%s", 
                   model_path, use_gpu)

        # Configure loggers for key modules
        key_modules = [
            'toolkit.parsers.sentence_parser',
            'toolkit.parsers.citation_utils',
            'toolkit.parsers.citation_parser',
            'toolkit.migration.corpus_processor',
            'toolkit.migration.corpus_db',
            'toolkit.migration.corpus_text',
            'toolkit.migration.line_processor',
            'toolkit.migration.sentence_processor'
        ]
        
        for module_name in key_modules:
            # Use migration logger for each module
            mod_logger = get_migration_logger(module_name.replace('toolkit.', ''))
            mod_logger.debug(f"Logger configured for {module_name}")

    def _get_attr_safe(self, obj: object, attr: str, default: Any = None) -> Any:
        """Safely get attribute from object."""
        try:
            return getattr(obj, attr, default)
        except (AttributeError, TypeError):
            return default

    def reset(self):
        """
        Reset the corpus processor state.
        
        Provides a hook for subclasses to reset internal state.
        """
        logger.debug("Resetting CorpusBase state")
