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
from app.models.text_line import TextLine, TextLineDB

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
            
            # Generate unique results ID
            results_id = str(uuid.uuid4())
            
            # Store citations in chunks to avoid Redis memory issues
            chunk_size = 1000
            total_chunks = (len(citations) + chunk_size - 1) // chunk_size
            
            # Store metadata about the results
            await self.redis.set(
                f"{settings.redis.SEARCH_RESULTS_PREFIX}{results_id}:meta",
                {
                    "total_results": len(citations),
                    "total_chunks": total_chunks,
                    "chunk_size": chunk_size
                },
                ttl=settings.redis.SEARCH_RESULTS_TTL
            )
            
            # Store each chunk
            for i in range(total_chunks):
                start = i * chunk_size
                end = start + chunk_size
                chunk = citations[start:end]
                
                # Convert Pydantic models to dicts for Redis storage
                chunk_data = [c.model_dump() for c in chunk]
                
                await self.redis.set(
                    f"{settings.redis.SEARCH_RESULTS_PREFIX}{results_id}:chunk:{i}",
                    chunk_data,
                    ttl=settings.redis.SEARCH_RESULTS_TTL
                )
            
            logger.info(f"Formatted and stored {len(citations)} citations with ID {results_id}")
            
            # Return results ID and first page of results
            return results_id, citations[:100]  # Return first 100 results
            
        except Exception as e:
            logger.error(f"Error formatting citations: {str(e)}", exc_info=True)
            raise

    async def get_paginated_results(self, results_id: str, page: int = 1, page_size: int = 100) -> List[Citation]:
        """Get a page of results from Redis."""
        try:
            # Get metadata
            meta = await self.redis.get(f"{settings.redis.SEARCH_RESULTS_PREFIX}{results_id}:meta")
            if not meta:
                logger.warning(f"No results found for ID {results_id}")
                return []
            
            total_results = meta["total_results"]
            chunk_size = meta["chunk_size"]
            
            # Calculate which chunk(s) we need
            start_index = (page - 1) * page_size
            end_index = min(start_index + page_size, total_results)
            
            # Check if requested page is beyond available results
            if start_index >= total_results:
                logger.warning(f"Requested page {page} is beyond available results (total pages: {(total_results + page_size - 1) // page_size})")
                return []
            
            start_chunk = start_index // chunk_size
            end_chunk = (end_index - 1) // chunk_size
            
            # Get required chunks
            citations = []
            for chunk_num in range(start_chunk, end_chunk + 1):
                chunk = await self.redis.get(f"{settings.redis.SEARCH_RESULTS_PREFIX}{results_id}:chunk:{chunk_num}")
                if chunk:
                    # Convert stored dicts back to Pydantic models
                    chunk_citations = [Citation.model_validate(c) for c in chunk]
                    citations.extend(chunk_citations)
                else:
                    logger.warning(f"Missing chunk {chunk_num} for results ID {results_id}")
            
            # Calculate slice within combined chunks
            chunk_start = start_index % chunk_size
            chunk_end = chunk_start + min(page_size, len(citations) - chunk_start)
            
            return citations[chunk_start:chunk_end]
            
        except Exception as e:
            logger.error(f"Error getting paginated results: {str(e)}", exc_info=True)
            raise

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
