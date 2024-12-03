"""
Service layer for managing lexical values.
Handles creation, retrieval, and management of lexical entries.
"""

from typing import Dict, Any, Optional, List, Tuple, Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text, func
import logging
import json
import time
import uuid

from app.core.pagination_config import PaginationConfig
from app.models.lexical_value import LexicalValue
from app.models.text_division import TextDivision
from app.models.text_line import TextLine
from app.models.sentence import Sentence, sentence_text_lines
from app.services.llm.lexical_service import LexicalLLMService
from app.services.llm.bedrock import BedrockClient
from app.services.citation_service import CitationService
from app.services.json_storage_service import JSONStorageService
from app.core.redis import redis_client
from app.core.citation_queries import (
    LEMMA_CITATION_QUERY,
    TEXT_CITATION_QUERY
)

# Use the standard logging configuration
logger = logging.getLogger(__name__)

class LexicalService:
    """Service for managing lexical values."""
    
    def __init__(self, session: AsyncSession):
        """Initialize the lexical service."""
        self.session = session
        
        # Initialize Bedrock client
        self.bedrock_client = BedrockClient()
        
        # Initialize Citation Service
        self.citation_service = CitationService(session)
        
        # Initialize Lexical LLM Service with both client and citation service
        self.lexical_llm = LexicalLLMService(
            client=self.bedrock_client, 
            citation_service=self.citation_service
        )
        
        self.json_storage = JSONStorageService()
        self.cache_ttl = 3600  # 1 hour cache TTL
        self.redis = redis_client
        self.DEFAULT_PAGE_SIZE = PaginationConfig.get_page_size('lexical_entries')
        logger.info(f"Initialized LexicalService with page size {self.DEFAULT_PAGE_SIZE}")
        logger.debug(f"Session initialized: {session}")

    async def _get_cached_value(self, lemma: str, version: Optional[str] = None) -> Optional[Dict]:
        """Get lexical value from cache with enhanced error handling and logging."""
        try:
            cache_key = f"lexical_value:{lemma}:{version}" if version else f"lexical_value:{lemma}"
            cached = await self.redis.get(cache_key)
            
            if cached:
                logger.info(f"Cache hit for lexical value: {lemma} (version: {version})")
                try:
                    return json.loads(cached)
                except json.JSONDecodeError as e:
                    logger.error(f"JSON decoding error for cached value {lemma}: {e}")
                    return None
            
            logger.debug(f"Cache miss for lexical value: {lemma} (version: {version})")
            return None
        
        except Exception as e:
            logger.error(f"Comprehensive cache retrieval error for {lemma}: {e}", exc_info=True)
            return None

    async def _cache_value(self, lemma: str, data: Dict, version: Optional[str] = None):
        """Cache lexical value data with enhanced error handling."""
        try:
            cache_key = f"lexical_value:{lemma}:{version}" if version else f"lexical_value:{lemma}"
            
            # Add additional logging for cache operations
            logger.debug(f"Attempting to cache {lemma} with key {cache_key}")
            
            await self.redis.set(
                cache_key,
                json.dumps(data),
                ttl=self.cache_ttl
            )
            logger.info(f"Successfully cached lexical value: {lemma} (version: {version})")
        except Exception as e:
            # More comprehensive error logging
            logger.error(f"Failed to cache lexical value {lemma}: {str(e)}", exc_info=True)

    async def _invalidate_cache(self, lemma: str):
        """Invalidate lexical value cache with improved logging."""
        try:
            # Get all versions
            versions = await self.get_json_versions(lemma)
            
            # Delete cache for current version
            await self.redis.delete(f"lexical_value:{lemma}")
            
            # Delete cache for all versions
            for version in versions:
                # Handle both string and object versions for backward compatibility
                version_id = version['version'] if isinstance(version, dict) else version
                await self.redis.delete(f"lexical_value:{lemma}:{version_id}")
                
            logger.info(f"Invalidated cache for lexical value: {lemma} and all versions")
        except Exception as e:
            logger.error(f"Failed to invalidate cache for {lemma}: {str(e)}", exc_info=True)

    async def _get_citations(self, word: str, search_lemma: bool) -> Tuple[str, List[Dict[str, Any]]]:
        """Get citations with full sentence context for a word/lemma."""
        try:
            logger.info(f"Getting citations for word: {word} (search_lemma: {search_lemma})")
            
            if search_lemma:
                # For lemma search, use the lemma citation query
                query = LEMMA_CITATION_QUERY
                params = {"pattern": word}
            else:
                # For text search, use the standard citation query with ILIKE pattern
                pattern = f'%{word}%'
                query = TEXT_CITATION_QUERY
                params = {"pattern": pattern}
            
            logger.debug(f"Executing citation query with params: {params}")
            
            try:
                # Execute query
                result = await self.session.execute(text(query), params)
                raw_results = result.mappings().all()
                
                # Log raw results for debugging
                logger.debug(f"Raw query results count: {len(raw_results)}")
                if raw_results:
                    logger.debug(f"First result sample: {dict(raw_results[0])}")
                
                if not raw_results:
                    logger.warning(f"No citations found in database for word: {word}")
                    return "", []
                
                # Format and store citations
                results_id, first_page = await self.citation_service.format_citations(raw_results)
                
                if not first_page:
                    logger.warning(f"No citations were formatted successfully for word: {word}")
                    return "", []
                
                # Get metadata to determine total pages
                meta_key = f"search_results:{results_id}:meta"
                meta = await self.redis.get(meta_key)
                
                if not meta:
                    logger.error(f"No metadata found for results ID {results_id}")
                    return "", []
                
                total_pages = meta.get("total_pages", 1)
                all_citations = []
                
                # Get all pages
                for page in range(1, total_pages + 1):
                    page_citations = await self.citation_service.get_paginated_results(results_id, page)
                    if page_citations:
                        all_citations.extend(page_citations)
                
                logger.info(f"Found and formatted {len(all_citations)} citations for {word}")
                return results_id, all_citations

            except Exception as e:
                logger.error(f"Database error executing citation query: {str(e)}", exc_info=True)
                raise ValueError(f"Failed to execute citation query: {str(e)}")

        except Exception as e:
            logger.error(f"Error getting citations for {word}: {str(e)}", exc_info=True)
            raise ValueError(f"Failed to get citations: {str(e)}")

    async def get_lexical_value(self, lemma: str, version: Optional[str] = None) -> Optional[LexicalValue]:
        """Get a lexical value by its lemma with linked citations, handling multiple entries."""
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

            # Query database for current version using a new session
            async with AsyncSession(self.session.bind) as db_session:
                query = (
                    select(LexicalValue)
                    .where(LexicalValue.lemma == lemma)
                    .join(Sentence, Sentence.id == LexicalValue.sentence_id, isouter=True)
                    .join(sentence_text_lines, sentence_text_lines.c.sentence_id == Sentence.id, isouter=True)
                    .join(TextLine, TextLine.id == sentence_text_lines.c.text_line_id, isouter=True)
                    .order_by(LexicalValue.id.desc())  # Order by most recent first
                )
                result = await db_session.execute(query)
                entries = result.scalars().all()
                
                if not entries:
                    return None
                
                if len(entries) > 1:
                    logger.warning(f"Multiple lexical entries found for lemma: {lemma}. Selecting the most recent entry.")
                
                # Select the first (most recent) entry
                entry = entries[0]
                
                # Cache and store in JSON for future requests
                entry_dict = entry.to_dict()
                await self._cache_value(lemma, entry_dict)
                self.json_storage.save(lemma, entry_dict)
                
                return entry
            
        except Exception as e:
            logger.error(f"Error getting lexical value for {lemma}: {str(e)}", exc_info=True)
            raise

    async def create_lexical_entry(
        self,
        lemma: str,
        search_lemma: bool = False,
        task_id: Optional[str] = None,
        llm_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a new lexical value entry with JSON storage."""
        start_time = time.time()
        logger.info(f"Starting creation of lexical entry for lemma: {lemma}")
        logger.debug(f"LLM config: {llm_config}")
        
        try:
            # Check if entry already exists - using a new session to avoid keeping it open
            async with AsyncSession(self.session.bind) as check_session:
                query = select(LexicalValue).where(LexicalValue.lemma == lemma)
                result = await check_session.execute(query)
                existing = result.scalar_one_or_none()
                if existing:
                    logger.info(f"Lexical value already exists for {lemma}")
                    return {
                        "success": False,
                        "message": "Lexical value already exists",
                        "entry": existing.to_dict(),
                        "action": "update"
                    }

            # Get citations with enhanced sentence context
            results_id, citations = await self._get_citations(lemma, search_lemma=True)
            
            if not citations:
                logger.error(f"No citations found for lemma: {lemma}")
                raise ValueError(f"No citations found for lemma: {lemma}")
            
            logger.info(f"Retrieved {len(citations)} citations for {lemma}")
            
            # Generate lexical value using LLM
            logger.info(f"Generating lexical value using LLM for {lemma}")
            analysis_result = await self.lexical_llm.create_lexical_value(
                word=lemma,
                citations=citations,
                llm_config=llm_config
            )
            
            # Extract dictionary from tuple if needed
            if isinstance(analysis_result, tuple):
                analysis = analysis_result[0]
            else:
                analysis = analysis_result
            
            # Validate the analysis data
            logger.info(f"Validating analysis data for {lemma}")
            self._validate_lexical_value(analysis)
            
            # Initialize sentence contexts
            sentence_contexts = {}
            for citation in citations:
                sentence_id = str(citation.sentence.id)
                sentence_contexts[sentence_id] = {
                    'text': citation.sentence.text,
                    'prev': citation.sentence.prev_sentence,
                    'next': citation.sentence.next_sentence,
                    'tokens': citation.sentence.tokens
                }
            
            # Set primary sentence ID and ensure all required fields are present
            if citations:
                analysis['sentence_id'] = int(citations[0].sentence.id)
            
            # Ensure all required fields are present with proper initialization
            analysis.update({
                'references': {'citations': [c.model_dump() for c in citations]},
                'sentence_contexts': sentence_contexts,
                'citations_used': analysis.get('citations_used', [])
            })

            # Create new entry in database
            async with AsyncSession(self.session.bind) as db_session:
                try:
                    logger.info(f"Creating database entry for {lemma}")
                    entry = LexicalValue.from_dict(analysis)
                    db_session.add(entry)
                    await db_session.commit()
                    await db_session.refresh(entry)
                    entry_dict = entry.to_dict()
                except Exception as db_error:
                    logger.error(f"Database error creating entry for {lemma}: {str(db_error)}")
                    raise
            
            # Store in JSON format with versioning and cache
            logger.debug(f"Entry dictionary: {entry_dict}")
            self.json_storage.save(lemma, entry_dict, create_version=True, llm_config=llm_config)
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

    def _validate_lexical_value(self, data: Union[Dict[str, Any], Tuple[Dict[str, Any], Dict[str, int]]]):
        """
        Validate lexical value data has all required fields.
        
        Handles both direct dictionary input and tuple input from LLM service.
        """
        # If input is a tuple, extract the first item (dictionary)
        if isinstance(data, tuple):
            data = data[0]
        
        # Validate input is a dictionary
        if not isinstance(data, dict):
            logger.error(f"Invalid input type for lexical value validation: {type(data)}")
            raise ValueError("Input must be a dictionary or a tuple containing a dictionary")
        
        # Define required fields
        required_fields = ['lemma', 'translation', 'short_description', 
                         'long_description', 'related_terms', 'citations_used']
        
        # Check for missing fields
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            logger.error(f"Missing required fields in lexical value data: {missing_fields}")
            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")

    async def update_lexical_value(
        self,
        lemma: str,
        data: Dict[str, Any],
        llm_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Update an existing lexical value."""
        try:
            # Use a new session for the update operation
            async with AsyncSession(self.session.bind) as db_session:
                query = select(LexicalValue).where(LexicalValue.lemma == lemma)
                result = await db_session.execute(query)
                entry = result.scalar_one_or_none()
                
                if not entry:
                    return {
                        "success": False,
                        "message": "Lexical value not found",
                        "action": "update"
                    }
            results_id, citations = await self._get_citations(lemma, search_lemma=True)
            
            if citations:
                # Generate new lexical value using LLM with updated config
                analysis_result = await self.lexical_llm.create_lexical_value(
                    word=lemma,
                    citations=citations,
                    llm_config=llm_config
                )
                
                # Extract dictionary from tuple if needed
                if isinstance(analysis_result, tuple):
                    analysis = analysis_result[0]
                else:
                    analysis = analysis_result
                
                # Update fields from analysis
                for key, value in analysis.items():
                    if hasattr(entry, key):
                        setattr(entry, key, value)

            await db_session.commit()
            await db_session.refresh(entry)
            
            # Update JSON storage with versioning and cache
            entry_dict = entry.to_dict()
            self.json_storage.save(lemma, entry_dict, create_version=True, llm_config=llm_config)
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

    async def get_json_versions(self, lemma: str) -> List[Dict[str, Any]]:
        """Get all available JSON versions for a lexical value with their metadata.
        
        Args:
            lemma: The lemma to get versions for
            
        Returns:
            List of dictionaries containing version info including model details and parameters
        """
        try:
            # Get detailed version info including model details
            versions = self.json_storage.list_versions(lemma)
            logger.info(f"Retrieved {len(versions)} versions for {lemma}")
            logger.debug(f"Version details: {json.dumps(versions, indent=2)}")
            return versions
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

    async def delete_lexical_value(self, lemma: str) -> bool:
        """Delete a lexical value."""
        try:
            success = False
            
            # Delete from database if it exists using a new session
            async with AsyncSession(self.session.bind) as db_session:
                query = select(LexicalValue).where(LexicalValue.lemma == lemma)
                result = await db_session.execute(query)
                entry = result.scalar_one_or_none()
                
                if entry:
                    await db_session.delete(entry)
                    await db_session.commit()
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
        limit: Optional[int] = None,
        page_size: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        List lexical values with dynamic pagination.
        
        Args:
            offset: Starting offset for results
            limit: Optional explicit limit
            page_size: Optional custom page size
        
        Returns:
            Dictionary with pagination metadata and results
        """
        try:
            # Use a new session for listing operations
            async with AsyncSession(self.session.bind) as db_session:
                # Determine effective page size
                effective_page_size = page_size or limit or self.DEFAULT_PAGE_SIZE
                
                # Count total lexical values
                count_query = select(func.count()).select_from(LexicalValue)
                total_count = await db_session.scalar(count_query)
                
                # Calculate pagination details
                total_pages = (total_count + effective_page_size - 1) // effective_page_size
                current_page = (offset // effective_page_size) + 1
                
                # Query lexical values with pagination
                query = (
                    select(LexicalValue)
                    .join(Sentence, Sentence.id == LexicalValue.sentence_id, isouter=True)
                    .join(sentence_text_lines, sentence_text_lines.c.sentence_id == Sentence.id, isouter=True)
                    .join(TextLine, TextLine.id == sentence_text_lines.c.text_line_id, isouter=True)
                    .offset(offset)
                    .limit(effective_page_size)
                )
                
                result = await db_session.execute(query)
                entries = result.scalars().all()
                
                # Convert to dictionaries
                entries_dict = [entry.to_dict() for entry in entries]
                
                # Prepare response with pagination metadata
                return {
                    "results": entries_dict,
                    "pagination": {
                        "total_results": total_count,
                        "total_pages": total_pages,
                        "current_page": current_page,
                        "page_size": effective_page_size,
                        "has_next": current_page < total_pages,
                        "has_previous": current_page > 1
                    }
                }
            
        except Exception as e:
            logger.error(f"Error listing lexical values: {str(e)}", exc_info=True)
            raise

    async def get_linked_citations(self, lemma: str) -> List[Dict[str, Any]]:
        """Get all citations directly linked to a lexical value."""
        try:
            results_id, citations = await self._get_citations(lemma, search_lemma=True)
            return citations
            
        except Exception as e:
            logger.error(f"Error getting linked citations for {lemma}: {str(e)}", exc_info=True)
            raise

