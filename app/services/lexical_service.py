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

from app.models.lexical_value import LexicalValue
from app.models.text_division import TextDivision
from app.services.llm_service import LLMService
from app.services.json_storage_service import JSONStorageService
from app.core.redis import redis_client

# Configure logging
logger = logging.getLogger(__name__)

class LexicalService:
    """Service for managing lexical values."""
    
    def __init__(self, session: AsyncSession):
        """Initialize the lexical service."""
        self.session = session
        self.llm_service = LLMService(session)
        self.json_storage = JSONStorageService()
        self.cache_ttl = 3600  # 1 hour cache TTL
        logger.info("Initialized LexicalService")

    async def _get_cached_value(self, lemma: str) -> Optional[Dict]:
        """Get lexical value from cache if available."""
        try:
            cache_key = f"lexical_value:{lemma}"
            cached = await redis_client.get(cache_key)
            if cached:
                logger.info(f"Cache hit for lexical value: {lemma}")
                return json.loads(cached)
            logger.info(f"Cache miss for lexical value: {lemma}")
            return None
        except Exception as e:
            logger.error(f"Cache error for lexical value {lemma}: {str(e)}")
            return None

    async def _cache_value(self, lemma: str, data: Dict):
        """Cache lexical value data."""
        try:
            cache_key = f"lexical_value:{lemma}"
            await redis_client.set(
                cache_key,
                json.dumps(data),
                ttl=self.cache_ttl
            )
            logger.info(f"Cached lexical value: {lemma}")
        except Exception as e:
            logger.error(f"Failed to cache lexical value {lemma}: {str(e)}")

    async def _invalidate_cache(self, lemma: str):
        """Invalidate lexical value cache."""
        try:
            cache_key = f"lexical_value:{lemma}"
            await redis_client.delete(cache_key)
            logger.info(f"Invalidated cache for lexical value: {lemma}")
        except Exception as e:
            logger.error(f"Failed to invalidate cache for {lemma}: {str(e)}")

    async def _get_citations(self, word: str, search_lemma: bool) -> List[Dict[str, Any]]:
        """Get citations with full sentence context for a word/lemma from the database."""
        try:
            logger.info(f"Getting citations for word: {word} (search_lemma: {search_lemma})")
            
            # Enhanced query to get complete sentence context and proper grouping
            if search_lemma:
                query = """
                WITH sentence_matches AS (
                    SELECT DISTINCT ON (s.id)
                        s.id as sentence_id,
                        s.content as sentence_text,
                        s.spacy_data as sentence_tokens,
                        tl.id as line_id,
                        tl.content as line_text,
                        tl.line_number,
                        td.id as division_id,
                        td.author_name,
                        td.work_name,
                        td.volume,
                        td.chapter,
                        td.section,
                        -- Get previous and next sentences for context
                        LAG(s.content) OVER (
                            PARTITION BY td.id 
                            ORDER BY tl.line_number
                        ) as prev_sentence,
                        LEAD(s.content) OVER (
                            PARTITION BY td.id 
                            ORDER BY tl.line_number
                        ) as next_sentence,
                        -- Group line numbers for the sentence
                        array_agg(tl.line_number) OVER (
                            PARTITION BY s.id
                        ) as line_numbers
                    FROM sentences s
                    JOIN text_lines tl ON s.text_line_id = tl.id
                    JOIN text_divisions td ON tl.division_id = td.id
                    WHERE CAST(s.spacy_data AS TEXT) ILIKE :pattern
                )
                SELECT * FROM sentence_matches
                """
                pattern = f'%"lemma":"{word}"%'
            else:
                query = """
                WITH sentence_matches AS (
                    SELECT DISTINCT ON (s.id)
                        s.id as sentence_id,
                        s.content as sentence_text,
                        s.spacy_data as sentence_tokens,
                        tl.id as line_id,
                        tl.content as line_text,
                        tl.line_number,
                        td.id as division_id,
                        td.author_name,
                        td.work_name,
                        td.volume,
                        td.chapter,
                        td.section,
                        -- Get previous and next sentences for context
                        LAG(s.content) OVER (
                            PARTITION BY td.id 
                            ORDER BY tl.line_number
                        ) as prev_sentence,
                        LEAD(s.content) OVER (
                            PARTITION BY td.id 
                            ORDER BY tl.line_number
                        ) as next_sentence,
                        -- Group line numbers for the sentence
                        array_agg(tl.line_number) OVER (
                            PARTITION BY s.id
                        ) as line_numbers
                    FROM sentences s
                    JOIN text_lines tl ON s.text_line_id = tl.id
                    JOIN text_divisions td ON tl.division_id = td.id
                    WHERE s.content ILIKE :pattern
                )
                SELECT * FROM sentence_matches
                """
                pattern = f'%{word}%'

            logger.debug(f"Executing citation query with pattern: {pattern}")
            logger.debug(f"Full SQL query:\n{query}")

            result = await self.session.execute(text(query), {"pattern": pattern})
            raw_results = result.mappings().all()
            logger.debug(f"Raw query results: {raw_results}")

            citations = []
            
            for row in raw_results:
                logger.debug(f"Processing row: {row}")
                # Get the text division for proper citation formatting
                division_query = select(TextDivision).where(TextDivision.id == row['division_id'])
                division_result = await self.session.execute(division_query)
                division = division_result.scalar_one()
                
                # Enhanced citation structure with full sentence context
                citation = {
                    "sentence": {
                        "id": str(row["sentence_id"]),
                        "text": row["sentence_text"],
                        "prev_sentence": row["prev_sentence"],
                        "next_sentence": row["next_sentence"],
                        "tokens": row["sentence_tokens"]
                    },
                    "citation": division.format_citation(),
                    "context": {
                        "line_id": str(row["line_id"]),
                        "line_text": row["line_text"],
                        "line_numbers": row["line_numbers"]
                    },
                    "location": {
                        "volume": row["volume"] or '',
                        "chapter": row["chapter"] or '',
                        "section": row["section"] or ''
                    },
                    "source": {
                        "author": row["author_name"] or 'Unknown',
                        "work": row["work_name"] or 'Unknown Work'
                    }
                }
                logger.debug(f"Formatted citation: {citation}")
                citations.append(citation)

            logger.info(f"Found {len(citations)} citations with sentence context for {word}")
            return citations

        except Exception as e:
            logger.error(f"Error getting citations for {word}: {str(e)}", exc_info=True)
            raise

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
            logger.info(f"Getting citations for {lemma}")
            citations = await self._get_citations(lemma, search_lemma)
            logger.debug(f"Retrieved {len(citations)} citations")
            
            # Generate lexical value using LLM
            logger.info(f"Generating lexical value using LLM for {lemma}")
            analysis = await self.llm_service.create_lexical_value(
                word=lemma,
                citations=citations
            )
            logger.debug(f"LLM analysis result: {analysis}")
            
            # Validate the analysis data
            logger.info(f"Validating analysis data for {lemma}")
            self._validate_lexical_value(analysis)
            
            # Store citations and sentence contexts in structured format
            analysis['references'] = {
                'citations': citations,
                'metadata': {
                    'search_lemma': search_lemma,
                    'total_citations': len(citations)
                }
            }
            
            # Extract sentence contexts and create direct links
            sentence_contexts = {}
            if citations:
                # Use the first citation's sentence for direct linking
                primary_citation = citations[0]
                analysis['sentence_id'] = primary_citation['sentence']['id']
                
                # Store all sentence contexts
                for citation in citations:
                    sentence_id = citation['sentence']['id']
                    sentence_contexts[sentence_id] = {
                        'text': citation['sentence']['text'],
                        'prev': citation['sentence']['prev_sentence'],
                        'next': citation['sentence']['next_sentence'],
                        'tokens': citation['sentence']['tokens']
                    }
            
            analysis['sentence_contexts'] = sentence_contexts
            
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

    async def get_lexical_value(self, lemma: str) -> Optional[LexicalValue]:
        """Get a lexical value by its lemma with linked citations."""
        try:
            # Try cache first
            cached = await self._get_cached_value(lemma)
            if cached:
                return LexicalValue.from_dict(cached)

            # Try JSON storage
            json_data = self.json_storage.load(lemma)
            if json_data:
                await self._cache_value(lemma, json_data)
                return LexicalValue.from_dict(json_data)

            # Query database
            query = select(LexicalValue).where(LexicalValue.lemma == lemma)
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
            entry = await self.get_lexical_value(lemma)
            if not entry:
                return False

            await self.session.delete(entry)
            await self.session.commit()
            
            # Delete from JSON storage
            self.json_storage.delete(lemma)
            
            # Invalidate cache
            await self._invalidate_cache(lemma)
            
            return True
            
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
            query = select(LexicalValue).offset(offset).limit(limit)
            result = await self.session.execute(query)
            entries = result.scalars().all()
            return [entry.to_dict() for entry in entries]
            
        except Exception as e:
            logger.error(f"Error listing lexical values: {str(e)}", exc_info=True)
            raise

    async def get_linked_citations(self, lemma: str) -> List[Dict[str, Any]]:
        """Get all citations directly linked to a lexical value."""
        try:
            entry = await self.get_lexical_value(lemma)
            if not entry:
                return []
                
            return entry.get_linked_citations()
            
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
