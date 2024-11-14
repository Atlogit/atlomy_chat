"""
Service for handling citation formatting and retrieval.
Provides consistent citation handling across the application.
"""

from typing import Dict, List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import logging
import uuid
import json

from app.core.redis import redis_client
from app.core.config import settings
from app.models.citations import (
    Citation, SentenceContext, CitationContext, 
    CitationLocation, CitationSource
)
from app.models.text_line import TextLine, TextLineAPI

# Configure logging
logger = logging.getLogger(__name__)

class CitationService:
    """Service for managing citations."""
    
    def __init__(self, session: AsyncSession):
        """Initialize the citation service."""
        self.session = session
        self.redis = redis_client
        logger.info("Initialized CitationService")

    async def format_citations(self, rows: List[Dict], bulk_fetch: bool = True) -> Tuple[str, List[Citation]]:
        """Format citations and store in Redis for pagination."""
        try:
            citations = []
            for row in rows:
                try:
                    citation = self._format_citation(row)
                    citations.append(citation)
                except Exception as e:
                    logger.error(f"Error formatting individual citation: {str(e)}", exc_info=True)
                    # Continue with other citations
                    continue
            
            if not citations:
                logger.warning("No citations were formatted successfully")
                return "", []
            
            # Generate unique results ID
            results_id = str(uuid.uuid4())
            
            # Store citations in chunks of 10 (page size)
            page_size = 10
            total_pages = (len(citations) + page_size - 1) // page_size
            
            # Store metadata
            meta = {
                "total_results": len(citations),
                "total_pages": total_pages,
                "page_size": page_size
            }
            
            meta_key = f"{settings.redis.SEARCH_RESULTS_PREFIX}{results_id}:meta"
            meta_success = await self.redis.set(
                meta_key,
                meta,
                ttl=settings.redis.SEARCH_RESULTS_TTL
            )
            
            if not meta_success:
                logger.error("Failed to store metadata in Redis")
                return "", []
            
            # Store each page
            all_pages_stored = True
            for page in range(total_pages):
                start = page * page_size
                end = min(start + page_size, len(citations))
                page_citations = citations[start:end]
                
                # Convert Pydantic models to dicts for Redis storage
                page_data = [c.model_dump() for c in page_citations]
                
                page_key = f"{settings.redis.SEARCH_RESULTS_PREFIX}{results_id}:page:{page + 1}"
                page_success = await self.redis.set(
                    page_key,
                    page_data,
                    ttl=settings.redis.SEARCH_RESULTS_TTL
                )
                
                if not page_success:
                    logger.error(f"Failed to store page {page + 1} in Redis")
                    all_pages_stored = False
                    break
                
                # Log first citation of each page
                if page_citations:
                    logger.debug(
                        f"Stored page {page + 1} ({len(page_citations)} citations): "
                        f"first citation ID={page_citations[0].sentence.id}"
                    )
            
            if not all_pages_stored:
                # Clean up any stored data
                await self.redis.delete(meta_key)
                pattern = f"{settings.redis.SEARCH_RESULTS_PREFIX}{results_id}:page:*"
                await self.redis.clear_cache(pattern)
                return "", []
            
            logger.info(f"Formatted and stored {len(citations)} citations with ID {results_id} in {total_pages} pages")
            
            # Return results ID and first page of results
            return results_id, citations[:page_size]  # Return first page
            
        except Exception as e:
            logger.error(f"Error formatting citations: {str(e)}", exc_info=True)
            raise

    async def get_paginated_results(self, results_id: str, page: int = 1, page_size: int = 10) -> List[Citation]:
        """Get a page of results from Redis."""
        try:
            # Get metadata
            meta_key = f"{settings.redis.SEARCH_RESULTS_PREFIX}{results_id}:meta"
            meta = await self.redis.get(meta_key)
            
            if not meta:
                logger.warning(f"No metadata found for results ID {results_id}")
                return []
            
            total_results = meta.get("total_results")
            total_pages = meta.get("total_pages")
            stored_page_size = meta.get("page_size")
            
            if not all([total_results, total_pages, stored_page_size]):
                logger.error(f"Invalid metadata for results ID {results_id}")
                return []
            
            # Check if requested page is beyond available pages
            if page > total_pages:
                logger.warning(f"Requested page {page} is beyond available pages ({total_pages})")
                return []
            
            # Get the requested page directly
            page_key = f"{settings.redis.SEARCH_RESULTS_PREFIX}{results_id}:page:{page}"
            page_data = await self.redis.get(page_key)
            
            if page_data is None:
                logger.warning(f"Missing page {page} for results ID {results_id}")
                return []
            
            try:
                # Convert stored dicts back to Pydantic models
                citations = [Citation.model_validate(c) for c in page_data]
                
                # Log page details
                if citations:
                    logger.debug(
                        f"Retrieved page {page} ({len(citations)} citations): "
                        f"first citation ID={citations[0].sentence.id}"
                    )
                
                return citations
                
            except Exception as e:
                logger.error(f"Error converting citations: {str(e)}")
                return []
            
        except Exception as e:
            logger.error(f"Error getting paginated results: {str(e)}", exc_info=True)
            return []

    def _format_citation(self, row: Dict) -> Citation:
        """Format a single citation directly from query result."""
        try:
            # Get line numbers and ensure it's a list
            line_numbers = row.get('line_numbers', [])
            if not isinstance(line_numbers, list):
                line_numbers = [line_numbers] if line_numbers else []
            
            # Format line number as range if needed
            line_value = None
            if line_numbers:
                if len(line_numbers) > 1:
                    line_value = f"{line_numbers[0]}-{line_numbers[-1]}"
                else:
                    line_value = str(line_numbers[0])
            
            # Create line ID if we have text ID
            line_id = ""
            if row.get('text_id') and line_numbers:
                line_id = f"{row['text_id']}-{line_numbers[0]}"
            
            # Handle tokens
            tokens = row.get("sentence_tokens", [])
            if isinstance(tokens, dict) and 'tokens' in tokens:
                tokens = tokens['tokens']
            elif not isinstance(tokens, list):
                tokens = []
            
            # Create sentence context
            sentence = SentenceContext(
                id=str(row.get("sentence_id", "")),
                text=row.get("sentence_text", ""),
                prev_sentence=row.get("prev_sentence"),
                next_sentence=row.get("next_sentence"),
                tokens=tokens
            )
            
            # Create citation context
            context = CitationContext(
                line_id=line_id,
                line_text=row.get("line_text", row.get("sentence_text", "")),
                line_numbers=line_numbers
            )
            
            # Create location
            location = CitationLocation(
                volume=row.get("volume"),
                book=row.get("book"),
                chapter=row.get("chapter"),
                section=row.get("section"),
                page=row.get("page"),
                fragment=row.get("fragment"),
                line=line_value
            )
            
            # Create source
            source = CitationSource(
                author=row.get("author_name", "Unknown"),
                work=row.get("work_name", "Unknown"),
                author_id=row.get("author_id_field"),
                work_id=row.get("work_number_field")
            )
            
            # Create full citation
            citation = Citation(
                sentence=sentence,
                citation=self._format_citation_text(row),
                context=context,
                location=location,
                source=source
            )
            
            return citation
            
        except Exception as e:
            logger.error(f"Error formatting citation: {str(e)}", exc_info=True)
            raise

    def _format_citation_text(self, row: Dict, abbreviated: bool = False) -> str:
        """Format citation as text string directly from query result."""
        try:
            if abbreviated:
                # Get abbreviated author name
                author = row.get("author_name", "")
                if author:
                    parts = author.split()
                    if parts:
                        # Get first 3 letters of first word
                        abbrev = parts[0][:3] + "."
                        # Add designation if present
                        if len(parts) > 1 and len(parts[-1]) <= 4:
                            abbrev += f" {parts[-1]}"
                        author = abbrev
                else:
                    author = row.get("author_id_field", "")

                # Get abbreviated work name
                work = row.get("work_name", "")
                if work:
                    words = work.split()
                    if words:
                        # Take first letter of each significant word
                        abbrev = ""
                        for word in words:
                            if word.lower() not in ["de", "in", "et", "ad", "the", "a", "an"]:
                                if word:
                                    abbrev += word[0].upper()
                        # If no abbreviation was created, use first 3 letters
                        if not abbrev and words:
                            abbrev = words[0][:3].capitalize()
                        work = abbrev + "."
                else:
                    work = row.get("work_number_field", "")

                # Start with author and work
                citation = f"{author} {work}"

                # Add location components in standard order
                for field in ["fragment", "volume", "book", "chapter", "page", "section"]:
                    if row.get(field):
                        citation += f".{row[field]}"

                # Add line number if present
                line_numbers = row.get('line_numbers', [])
                if line_numbers:
                    if len(line_numbers) > 1:
                        citation += f".{line_numbers[0]}-{line_numbers[-1]}"
                    else:
                        citation += f".{line_numbers[0]}"

                return citation.strip()
            else:
                # Full citation format
                author = row.get("author_name", row.get("author_id_field", "Unknown"))
                work = row.get("work_name", row.get("work_number_field", "Unknown"))
                citation = f"{author}, {work}"

                # Add location components
                components = []
                field_labels = {
                    "fragment": "Fragment",
                    "volume": "Volume",
                    "book": "Book",
                    "chapter": "Chapter",
                    "page": "Page",
                    "section": "Section"
                }

                for field, label in field_labels.items():
                    if row.get(field):
                        components.append(f"{label} {row[field]}")

                # Add line number if present
                line_numbers = row.get('line_numbers', [])
                if line_numbers:
                    if len(line_numbers) > 1:
                        components.append(f"Line {line_numbers[0]}-{line_numbers[-1]}")
                    else:
                        components.append(f"Line {line_numbers[0]}")

                if components:
                    citation += f", {', '.join(components)}"

                return citation
            
        except Exception as e:
            logger.error(f"Error formatting citation text: {str(e)}", exc_info=True)
            raise
