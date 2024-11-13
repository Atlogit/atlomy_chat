"""
Singleton class for shared processing components.

Provides centralized access to shared resources like parsers and NLP pipeline.
"""

import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from toolkit.parsers.sentence import SentenceParser
from toolkit.parsers.citation import CitationParser
from toolkit.nlp.pipeline import NLPPipeline

logger = logging.getLogger(__name__)

class SharedComponents:
    """Singleton class for shared processing components."""
    
    _instance = None
    _sentence_parser = None
    _citation_parser = None
    _nlp_pipeline = None
    
    @classmethod
    def get_instance(cls, session: Optional[AsyncSession] = None, 
                    model_path: Optional[str] = None,
                    use_gpu: Optional[bool] = None) -> 'SharedComponents':
        """Get or create the singleton instance."""
        if cls._instance is None:
            if session is None:
                raise ValueError("Session is required for initial SharedComponents creation")
            cls._instance = cls(session, model_path, use_gpu)
            logger.info("Created new SharedComponents instance")
        return cls._instance
    
    def __init__(self, session: AsyncSession, 
                 model_path: Optional[str] = None,
                 use_gpu: Optional[bool] = None):
        """Initialize shared components.
        
        Args:
            session: SQLAlchemy async session
            model_path: Optional path to spaCy model
            use_gpu: Whether to use GPU for NLP processing
        """
        # Prevent direct instantiation
        if SharedComponents._instance is not None:
            raise RuntimeError("Use get_instance() to access SharedComponents")
            
        self.session = session
        self._model_path = model_path
        self._use_gpu = use_gpu
        logger.info("Initialized shared components with model_path=%s, use_gpu=%s",
                   model_path, use_gpu)
    
    @property
    def sentence_parser(self):
        """Get or create SentenceParser instance."""
        if self._sentence_parser is None:
            self._sentence_parser = SentenceParser.get_instance()
        return self._sentence_parser
    
    @property
    def citation_parser(self):
        """Get or create CitationParser instance."""
        if self._citation_parser is None:
            self._citation_parser = CitationParser.get_instance()
        return self._citation_parser
    
    @property
    def nlp_pipeline(self):
        """Get or create NLPPipeline instance."""
        if self._nlp_pipeline is None:
            self._nlp_pipeline = NLPPipeline(
                model_path=self._model_path,
                use_gpu=self._use_gpu
            )
        return self._nlp_pipeline
    
    def reset(self):
        """Reset stateful components."""
        if self._citation_parser:
            self._citation_parser.reset()
        # Add any other necessary reset logic for components
        logger.debug("Reset shared components state")
