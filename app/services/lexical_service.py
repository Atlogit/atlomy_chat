"""
Service layer for managing lexical values.
Handles creation, retrieval, and management of lexical entries.
"""

from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
import logging
import json
import time
import uuid

from app.models.lexical_value import LexicalValue
from app.models.text_division import TextDivision
from app.models.text_line import TextLine
from app.models.sentence import Sentence, sentence_text_lines
from app.services.llm_service import LLMService
from app.services.citation_service import CitationService
from app.services.json_storage_service import JSONStorageService
from app.core.redis import redis_client
from app.core.citation_queries import (
    LEMMA_CITATION_QUERY,
    TEXT_CITATION_QUERY,
    DIRECT_SENTENCE_QUERY
)

# Configure logging
logger = logging.getLogger(__name__)

class LexicalService:
    """Service for managing lexical values."""
    
    def __init__(self, session: AsyncSession):
        """Initialize the lexical service."""
        self.session = session
        self.llm_service = LLMService(session)
        self.citation_service = CitationService(session)
        self.json_storage = JSONStorageService()
        self.cache_ttl = 3600  # 1 hour cache TTL
        logger.info("Initialized LexicalService")

    async def _get_cached_value(self, lemma: str, version: Optional[str] = None) -> Optional[Dict]:
        """Get lexical value from cache if available."""
        try:
            cache_key = f"lexical_value:{lemma}:{version}" if version else f"lexical_value:{lemma}"
            cached = await redis_client.get(cache_key)
            if cached:
                logger.info(f"Cache hit for lexical value: {lemma} (version: {version})")
                return json.loads(cached)
            else:
                logger.info(f"Cache miss for lexical value: {lemma} (version: {version})")
                return None
        except Exception as e:
            logger.error(f"Cache error for lexical value {lemma}: {str(e)}")
            return None

    async def _cache_value(self, lemma: str, data: Dict, version: Optional[str] = None):
        """Cache lexical value data."""
        try:
            cache_key = f"lexical_value:{lemma}:{version}" if version else f"lexical_value:{lemma}"
            await redis_client.set(
                cache_key,
                json.dumps(data),
                ttl=self.cache_ttl
            )
            logger.info(f"Cached lexical value: {lemma} (version: {version})")
        except Exception as e:
            logger.error(f"Failed to cache lexical value {lemma}: {str(e)}")

    async def _invalidate_cache(self, lemma: str):
        """Invalidate lexical value cache."""
        try:
            # Get all versions
            versions = await self.get_json_versions(lemma)
            
            # Delete cache for current version
            await redis_client.delete(f"lexical_value:{lemma}")
            
            # Delete cache for all versions
            for version in versions:
                await redis_client.delete(f"lexical_value:{lemma}:{version}")
                
            logger.info(f"Invalidated cache for lexical value: {lemma} and all versions")
        except Exception as e:
            logger.error(f"Failed to invalidate cache for {lemma}: {str(e)}")

    async def _get_citations(self, word: str, search_lemma: bool) -> List[Dict[str, Any]]:
        """Get citations with full sentence context for a word/lemma from the database."""
        try:
            logger.info(f"Getting citations for word: {word} (search_lemma: {search_lemma})")
            
            if search_lemma:
                # For lemma search, use the optimized direct sentence query
                query = DIRECT_SENTENCE_QUERY
                params = {"pattern": word}
            else:
                # For text search, use the standard citation query with ILIKE pattern
                pattern = f'%{word}%'
                query = TEXT_CITATION_QUERY
                params = {"pattern": pattern}
            
            logger.debug(f"Executing citation query with params: {params}")
            
            try:
                result = await self.session.execute(text(query), params)
                raw_results = result.mappings().all()
                
                # Use CitationService to format citations
                citations = await self.citation_service.format_citations(raw_results)
                
                logger.info(f"Found {len(citations)} citations for {word}")
                return citations

            except Exception as e:
                logger.error(f"Database error executing citation query: {str(e)}", exc_info=True)
                raise ValueError(f"Failed to execute citation query: {str(e)}")

        except Exception as e:
            logger.error(f"Error getting citations for {word}: {str(e)}", exc_info=True)
            raise ValueError(f"Failed to get citations: {str(e)}")

    def _validate_lexical_value(self, data: Dict[str, Any]):
        """Validate lexical value data has all required fields."""
        required_fields = ['lemma', 'translation', 'short_description', 
                         'long_description', 'related_terms', 'citations_used']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            logger.error(f"Missing required fields in lexical value data: {missing_fields}")
            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")

    async def create_lexical_entry(
        self,
        lemma: str,
        search_lemma: bool = False,
        task_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new lexical value entry with JSON storage."""
        start_time = time.time()
        logger.info(f"Starting creation of lexical entry for lemma: {lemma}")
        
        try:
            # Check if entry already exists
            existing = await self.get_lexical_value(lemma)
            if existing:
                logger.info(f"Lexical value already exists for {lemma}")
                return {
                    "success": False,
                    "message": "Lexical value already exists",
                    "entry": existing.to_dict(),
                    "action": "update"
                }

            # Get citations with enhanced sentence context
            citations = await self._get_citations(lemma, search_lemma=True)
            logger.info(f"Retrieved {len(citations)} citations for {lemma}")
            
            # Generate lexical value using LLM
            logger.info(f"Generating lexical value using LLM for {lemma}")
            analysis = await self.llm_service.create_lexical_value(
                word=lemma,
                citations=citations
            )
            
            # Validate the analysis data
            logger.info(f"Validating analysis data for {lemma}")
            self._validate_lexical_value(analysis)
            
            # Initialize sentence contexts
            sentence_contexts = {}
            if citations:
                for citation in citations:
                    sentence_id = str(citation['sentence']['id'])
                    sentence_contexts[sentence_id] = {
                        'text': citation['sentence']['text'],
                        'prev': citation['sentence']['prev_sentence'],
                        'next': citation['sentence']['next_sentence'],
                        'tokens': citation['sentence']['tokens']
                    }
            
            # Set primary sentence ID and ensure all required fields are present
            if citations:
                analysis['sentence_id'] = int(citations[0]['sentence']['id'])
            
            # Ensure all required fields are present with proper initialization
            analysis.update({
                'references': {'citations': citations},  # Store formatted citations properly
                'sentence_contexts': sentence_contexts,  # Store sentence contexts
                'citations_used': analysis.get('citations_used', [])  # Keep LLM's citation analysis
            })
            
            # Create new entry in database
            logger.info(f"Creating database entry for {lemma}")
            entry = LexicalValue.from_dict(analysis)
            self.session.add(entry)
            await self.session.commit()
            await self.session.refresh(entry)
            
            # Store in JSON format
            entry_dict = entry.to_dict()
            logger.debug(f"Entry dictionary: {entry_dict}")
            self.json_storage.save(lemma, entry_dict)
            
            # Cache the new entry
            await self._cache_value(lemma, entry_dict)
            
            duration = time.time() - start_time
            logger.info(f"Created lexical value for {lemma} in {duration:.2f}s")
            
            return {
                "success": True,
                "message": "Lexical value created successfully",
                "entry": entry_dict,
                "action": "create"
            }
            
        except Exception as e:
            logger.error(f"Error creating lexical value for {lemma}: {str(e)}", exc_info=True)
            raise

    async def get_lexical_value(self, lemma: str, version: Optional[str] = None) -> Optional[LexicalValue]:
        """Get a lexical value by its lemma with linked citations."""
        try:
            # Try cache first
            cached = await self._get_cached_value(lemma, version)
            if cached:
                return LexicalValue.from_dict(cached)

            # Try JSON storage with version
            json_data = self.json_storage.load(lemma, version)
            if json_data:
                await self._cache_value(lemma, json_data, version)
                return LexicalValue.from_dict(json_data)

            # If version was requested but not found, return None
            if version:
                return None

            # Query database for current version
            query = (
                select(LexicalValue)
                .where(LexicalValue.lemma == lemma)
                .join(Sentence, Sentence.id == LexicalValue.sentence_id, isouter=True)
                .join(sentence_text_lines, sentence_text_lines.c.sentence_id == Sentence.id, isouter=True)
                .join(TextLine, TextLine.id == sentence_text_lines.c.text_line_id, isouter=True)
            )
            result = await self.session.execute(query)
            entry = result.scalar_one_or_none()
            
            if entry:
                # Cache and store in JSON for future requests
                entry_dict = entry.to_dict()
                await self._cache_value(lemma, entry_dict)
                self.json_storage.save(lemma, entry_dict)
                
            return entry
            
        except Exception as e:
            logger.error(f"Error getting lexical value for {lemma}: {str(e)}", exc_info=True)
            raise

    async def update_lexical_value(
        self,
        lemma: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update an existing lexical value."""
        try:
            entry = await self.get_lexical_value(lemma)
            if not entry:
                return {
                    "success": False,
                    "message": "Lexical value not found",
                    "action": "update"
                }

            # Update fields
            for key, value in data.items():
                if hasattr(entry, key):
                    if key == 'sentence_id' and value:
                        # Ensure integer conversion for sentence_id
                        setattr(entry, key, int(value))
                    else:
                        setattr(entry, key, value)

            await self.session.commit()
            await self.session.refresh(entry)
            
            # Update JSON storage
            entry_dict = entry.to_dict()
            self.json_storage.save(lemma, entry_dict)
            
            # Invalidate cache
            await self._invalidate_cache(lemma)
            
            return {
                "success": True,
                "message": "Lexical value updated successfully",
                "entry": entry_dict,
                "action": "update"
            }
            
        except Exception as e:
            logger.error(f"Error updating lexical value for {lemma}: {str(e)}", exc_info=True)
            raise

    async def delete_lexical_value(self, lemma: str) -> bool:
        """Delete a lexical value."""
        try:
            success = False
            
            # Delete from database if it exists
            query = select(LexicalValue).where(LexicalValue.lemma == lemma)
            result = await self.session.execute(query)
            entry = result.scalar_one_or_none()
            
            if entry:
                await self.session.delete(entry)
                await self.session.commit()
                success = True
            
            # Always try to delete from JSON storage
            try:
                self.json_storage.delete(lemma)
                success = True
            except Exception as e:
                logger.warning(f"Error deleting JSON storage for {lemma}: {str(e)}")
                # Don't raise here, as we want to continue with cache invalidation
            
            # Always invalidate cache
            await self._invalidate_cache(lemma)
            
            return success
            
        except Exception as e:
            logger.error(f"Error deleting lexical value for {lemma}: {str(e)}", exc_info=True)
            raise

    async def list_lexical_values(
        self,
        offset: int = 0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """List lexical values with pagination."""
        try:
            query = (
                select(LexicalValue)
                .join(Sentence, Sentence.id == LexicalValue.sentence_id, isouter=True)
                .join(sentence_text_lines, sentence_text_lines.c.sentence_id == Sentence.id, isouter=True)
                .join(TextLine, TextLine.id == sentence_text_lines.c.text_line_id, isouter=True)
                .offset(offset)
                .limit(limit)
            )
            result = await self.session.execute(query)
            entries = result.scalars().all()
            return [entry.to_dict() for entry in entries]
            
        except Exception as e:
            logger.error(f"Error listing lexical values: {str(e)}", exc_info=True)
            raise

    async def get_linked_citations(self, lemma: str) -> List[Dict[str, Any]]:
        """Get all citations directly linked to a lexical value."""
        try:
            citations = await self._get_citations(lemma, search_lemma=True)
            return citations
            
        except Exception as e:
            logger.error(f"Error getting linked citations for {lemma}: {str(e)}", exc_info=True)
            raise

    async def get_json_versions(self, lemma: str) -> List[str]:
        """Get all available JSON versions for a lexical value."""
        try:
            return self.json_storage.list_versions(lemma)
        except Exception as e:
            logger.error(f"Error getting JSON versions for {lemma}: {str(e)}", exc_info=True)
            raise

    async def get_storage_info(self) -> Dict[str, Any]:
        """Get information about JSON storage."""
        try:
            return self.json_storage.get_storage_info()
        except Exception as e:
            logger.error(f"Error getting storage info: {str(e)}", exc_info=True)
            raise
