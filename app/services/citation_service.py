"""
Service for handling citation formatting and retrieval.
Provides consistent citation handling across the application.
"""

from typing import Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import logging

from app.models.text_division import TextDivision

# Configure logging
logger = logging.getLogger(__name__)

class CitationService:
    """Service for managing citations."""
    
    def __init__(self, session: AsyncSession):
        """Initialize the citation service."""
        self.session = session
        logger.info("Initialized CitationService")

    async def format_citations(self, rows: List[Dict], bulk_fetch: bool = True) -> List[Dict]:
        """Format citations with optional bulk division fetching."""
        try:
            # Bulk fetch divisions if needed
            divisions = await self._fetch_divisions(rows) if bulk_fetch else {}
            
            citations = [
                self._format_citation(row, divisions.get(row.get('division_id'))) 
                for row in rows
            ]
            
            logger.info(f"Formatted {len(citations)} citations")
            logger.debug(f"First citation: {citations[0] if citations else None}")
            return citations
            
        except Exception as e:
            logger.error(f"Error formatting citations: {str(e)}", exc_info=True)
            raise

    async def _fetch_divisions(self, rows: List[Dict]) -> Dict:
        """Fetch text divisions in bulk for better performance."""
        try:
            # Extract division IDs from rows
            division_ids = {
                row.get('division_id') 
                for row in rows 
                if row.get('division_id')
            }
            
            if not division_ids:
                return {}
                
            # Fetch all divisions in one query with proper author join
            divisions_query = text("""
                SELECT td.*, t.title, t.id as text_id, a.name as author_name
                FROM text_divisions td
                JOIN texts t ON td.text_id = t.id
                LEFT JOIN authors a ON t.author_id = a.id
                WHERE td.id = ANY(:ids)
            """)
            
            result = await self.session.execute(
                divisions_query, 
                {"ids": list(division_ids)}
            )
            
            divisions = {d['id']: d for d in result.mappings().all()}
            logger.info(f"Fetched {len(divisions)} divisions")
            logger.debug(f"First division: {next(iter(divisions.values())) if divisions else None}")
            return divisions
            
        except Exception as e:
            logger.error(f"Error fetching divisions: {str(e)}", exc_info=True)
            raise

    def _format_citation(self, row: Dict, division_data: Optional[Dict] = None) -> Dict:
        """Format a single citation with proper structure."""
        try:
            # Get line number and ensure it's a list
            line_numbers = row.get('line_numbers', [])
            if not isinstance(line_numbers, list):
                line_numbers = [line_numbers] if line_numbers else []
            
            # Create line ID if we have both text ID and line number
            line_id = ""
            if division_data and division_data.get('text_id') and line_numbers:
                line_id = f"{division_data['text_id']}-{line_numbers[0]}"
            
            # Get author name in order of preference
            author_name = (
                row.get('author_name') or  # From the main query
                (division_data.get('author_name') if division_data else None) or  # From division data
                row.get('author_id_field')  # Fallback to ID field
            )
            
            # Get work name in order of preference
            work_name = (
                row.get('work_name') or  # From the main query
                (division_data.get('title') if division_data else None) or  # From division data
                row.get('work_number_field')  # Fallback to ID field
            )

            # Handle tokens - ensure we get just the array part if it's wrapped in an object
            tokens = row.get("sentence_tokens", [])
            if isinstance(tokens, dict) and 'tokens' in tokens:
                tokens = tokens['tokens']
            elif not isinstance(tokens, list):
                tokens = []
            
            # Format line number as range if needed
            line_value = None
            if line_numbers:
                if len(line_numbers) > 1:
                    line_value = f"{line_numbers[0]}-{line_numbers[-1]}"
                else:
                    line_value = str(line_numbers[0])
            
            # Build citation structure
            citation = {
                "sentence": {
                    "id": str(row.get("sentence_id", "")),
                    "text": row.get("sentence_text", ""),
                    "prev_sentence": row.get("prev_sentence"),
                    "next_sentence": row.get("next_sentence"),
                    "tokens": tokens
                },
                "citation": "",  # Will be set after creating TextDivision
                "context": {
                    "line_id": line_id,
                    "line_text": row.get("line_text", row.get("sentence_text", "")),
                    "line_numbers": line_numbers
                },
                "location": {
                    "volume": row.get("volume"),
                    "book": row.get("book"),  # Add book field
                    "chapter": row.get("chapter"),
                    "section": row.get("section"),
                    "page": row.get("page"),
                    "fragment": row.get("fragment"),
                    "line": line_value
                },
                "source": {
                    "author": author_name if author_name else "Unknown",
                    "work": work_name if work_name else "Unknown",
                    "author_id": row.get("author_id_field"),
                    "work_id": row.get("work_number_field")
                }
            }
            
            # Create TextDivision for citation formatting
            division = TextDivision()
            if division_data:
                for key, value in division_data.items():
                    setattr(division, key, value)
            
            # Set author and work information explicitly
            division.author_name = author_name
            division.work_name = work_name
            division.author_id_field = row.get("author_id_field")
            division.work_number_field = row.get("work_number_field")
            
            # Set location fields
            for field in ["volume", "book", "chapter", "section", "page", "line", "fragment"]:  # Add book to fields
                value = citation["location"].get(field)
                if value:
                    setattr(division, field, value)
            
            # Format citation using TextDivision
            citation["citation"] = division.format_citation()
            
            return citation
            
        except Exception as e:
            logger.error(f"Error formatting citation: {str(e)}", exc_info=True)
            raise
    def format_citation_text(self, citation: Dict, abbreviated: bool = False) -> str:
        """Format a citation as a text string."""
        try:
            # Create TextDivision instance for formatting
            division = TextDivision(
                author_name=citation['source']['author'],
                work_name=citation['source']['work'],
                author_id_field=citation['source'].get('author_id'),
                work_number_field=citation['source'].get('work_id')
            )
            
            # Set location fields
            for field in ["volume", "chapter", "section", "page", "fragment"]:
                value = citation["location"].get(field)
                if value:
                    setattr(division, field, value)
            
            # Set line number from context as a range if needed
            if citation.get('context', {}).get('line_numbers'):
                line_numbers = citation['context']['line_numbers']
                if len(line_numbers) > 1:
                    # If multiple lines, use range format (e.g., "1-3")
                    division.line = f"{line_numbers[0]}-{line_numbers[-1]}"
                else:
                    # Single line
                    division.line = str(line_numbers[0])
            
            # Format citation using TextDivision's method
            citation_text = division.format_citation(abbreviated=abbreviated)
            
            # Append sentence text if available
            if citation['sentence'].get('text'):
                citation_text += f": {citation['sentence']['text']}"
            
            return citation_text
            
        except Exception as e:
            logger.error(f"Error formatting citation text: {str(e)}", exc_info=True)
            raise
