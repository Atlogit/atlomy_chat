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
                
            # Fetch all divisions in one query
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
            
            return divisions
            
        except Exception as e:
            logger.error(f"Error fetching divisions: {str(e)}", exc_info=True)
            raise

    def _format_citation(self, row: Dict, division_data: Optional[Dict] = None) -> Dict:
        """Format a single citation with proper structure."""
        try:
            # Create and populate TextDivision instance
            division = TextDivision()
            if division_data:
                for key, value in division_data.items():
                    setattr(division, key, value)
            
            # Get line number and ensure it's a list
            line_number = row.get("min_line_number")
            line_numbers = [line_number] if line_number else []
            
            # Create line ID if we have both text ID and line number
            line_id = ""
            if division_data and division_data.get('text_id') and line_number:
                line_id = f"{division_data['text_id']}-{line_number}"
            
            # Use author_name directly from the row data
            author_name = row.get('author_name')
            if not author_name and division_data:
                author_name = division_data.get('author_name')
            
            # Use work_name directly from the row data
            work_name = row.get('work_name')
            if not work_name and division_data:
                work_name = division_data.get('work_name')
            
            # Build citation structure
            citation = {
                "sentence": {
                    "id": str(row.get("sentence_id", "")),
                    "text": row.get("sentence_text", ""),
                    "prev_sentence": row.get("prev_sentence"),
                    "next_sentence": row.get("next_sentence"),
                    "tokens": row.get("sentence_tokens", {})
                },
                "citation": "",  # Will be set after creating TextDivision
                "context": {
                    "line_id": line_id,
                    "line_text": row.get("line_text", row.get("sentence_text", "")),
                    "line_numbers": line_numbers
                },
                "location": {
                    "volume": row.get("volume"),
                    "chapter": row.get("chapter"),
                    "section": row.get("section")
                },
                "source": {
                    "author": author_name or row.get('author_id_field', 'Unknown'),
                    "work": work_name or row.get('work_number_field', '')
                }
            }
            
            # Create TextDivision for citation formatting
            division = TextDivision()
            if division_data:
                for key, value in division_data.items():
                    setattr(division, key, value)
            
            # Set author and work names explicitly
            division.author_name = author_name
            division.work_name = work_name
            
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
                volume=citation['location'].get('volume'),
                chapter=citation['location'].get('chapter'),
                line=citation['context'].get('line_numbers', [None])[0],
                section=citation['location'].get('section')
            )
            
            # Format citation using TextDivision's method
            citation_text = division.format_citation(abbreviated=abbreviated)
            
            # Append sentence text if available
            if citation['sentence'].get('text'):
                citation_text += f": {citation['sentence']['text']}"
            
            return citation_text
            
        except Exception as e:
            logger.error(f"Error formatting citation text: {str(e)}", exc_info=True)
            raise
