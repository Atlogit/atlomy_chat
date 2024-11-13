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

# Create logs directory if it doesn't exist
os.makedirs('logs', exist_ok=True)

# Configure logging
logger = logging.getLogger('corpus_processing')
logger.setLevel(logging.DEBUG)

# Create formatters
file_formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
)
console_formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# File handler - use timestamp in filename
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
file_handler = logging.FileHandler(f'logs/corpus_processing_{timestamp}.log')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(file_formatter)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(console_formatter)

# Add handlers to logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Set debug level for key modules
for module in [
    'toolkit.parsers.sentence_parser',
    'toolkit.parsers.citation_utils',  # Added citation modules
    'toolkit.parsers.citation_parser',
    'toolkit.migration.corpus_processor',
    'toolkit.migration.corpus_db',
    'toolkit.migration.corpus_text',
    'toolkit.migration.line_processor',
    'toolkit.migration.sentence_processor'
]:
    mod_logger = logging.getLogger(module)
    mod_logger.setLevel(logging.DEBUG)
    mod_logger.addHandler(file_handler)
    mod_logger.addHandler(console_handler)

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

    def _get_attr_safe(self, obj: object, attr: str, default: Any = None) -> Any:
        """Safely get attribute from object."""
        try:
            return getattr(obj, attr, default)
        except (AttributeError, TypeError):
            return default
