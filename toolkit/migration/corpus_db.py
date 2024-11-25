"""
Database operations for corpus processing.

Handles database interactions for corpus text processing.
"""

from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy import select, and_, case
from tqdm import tqdm

from app.models.text import Text
from app.models.text_line import TextLine
from app.models.text_division import TextDivision
from app.models.sentence import sentence_text_lines, Sentence as Sentence_Model
from toolkit.parsers.text import TextLine as ParserTextLine
from toolkit.parsers.sentence import Sentence
from toolkit.parsers.citation_utils import map_level_to_field

from .corpus_nlp import CorpusNLP

# Import migration logging configuration
from toolkit.migration.logging_config import get_migration_logger

# Use migration logger instead of standard logger
logger = get_migration_logger('migration.corpus_db')

class CorpusDB(CorpusNLP):
    """Database operations for corpus processing."""

    def _convert_to_parser_text_line(self, db_line: TextLine, division: TextDivision) -> ParserTextLine:
        """Convert database TextLine to parser TextLine."""
        # Get line number as integer
        line_number = None
        if db_line.line_number is not None:
            try:
                line_number = int(db_line.line_number)
            except (ValueError, TypeError):
                pass
                
        # Create parser line with title flag
        parser_line = ParserTextLine(
            content=db_line.content,
            line_number=line_number,  # Now an integer or None
            is_title=db_line.is_title  # Preserve title flag
        )
        return parser_line

    def _get_parent_field(self, line: TextLine) -> Tuple[Optional[str], Optional[str]]:
        """Get the parent field and value for a line based on work structure."""
        if not hasattr(line, 'citation') or not line.citation:
            return None, None
            
        structure = self.citation_parser.get_work_structure(
            line.citation.author_id,
            line.citation.work_id
        )
        if not structure:
            return None, None
            
        # Convert structure to lowercase for consistent comparison
        structure_levels = [level.lower() for level in structure]
        
        # Find 'line' in structure and get its parent
        try:
            line_index = structure_levels.index('line')
            if line_index > 0:  # If 'line' has a parent level
                parent_level = structure_levels[line_index - 1]
                # Map parent level to database field
                parent_field = map_level_to_field(parent_level, structure)
                # Get parent value from citation hierarchy levels
                if line.citation.hierarchy_levels and parent_field in line.citation.hierarchy_levels:
                    parent_value = line.citation.hierarchy_levels[parent_field]
                    return parent_field, parent_value
        except ValueError:
            pass
            
        return None, None

    def _get_line_number(self, line: TextLine) -> Optional[int]:
        """Get line number from citation hierarchy levels."""
        # First try to get line number directly from the line object
        if hasattr(line, 'line_number') and line.line_number is not None:
            try:
                return int(line.line_number)
            except (ValueError, TypeError):
                pass
            
        # If no direct line number, try to get from citation
        if not hasattr(line, 'citation') or not line.citation or not line.citation.hierarchy_levels:
            return None
            
        # Get work structure using citation parser
        structure = self.citation_parser.get_work_structure(
            line.citation.author_id,
            line.citation.work_id
        )
        if not structure:
            return None
            
        # Find the line level in the structure
        for level in structure:
            level_key = level.lower()
            if level_key == 'line' and level_key in line.citation.hierarchy_levels:
                line_value = line.citation.hierarchy_levels[level_key]
                if line_value:
                    # Clean line value to remove tab content
                    clean_value = line_value.split('\t')[0] if '\t' in line_value else line_value
                    try:
                        return int(clean_value)
                    except (ValueError, TypeError):
                        pass
                
        return None

    async def get_work_list(self) -> List[Text]:
        """Get list of all works."""
        try:
            result = await self.session.execute(select(Text))
            works = result.scalars().all()
            logger.debug("Found %d works", len(works))
            return works
        except Exception as e:
            logger.error("Error getting work list: %s", str(e))
            return []

    async def get_work(self, work_id: int) -> Optional[Text]:
        """Get work by ID."""
        try:
            result = await self.session.execute(
                select(Text).where(Text.id == work_id)
            )
            work = result.scalar_one_or_none()
            if work:
                logger.debug("Found work %d: %s", work_id, work.title)
            else:
                logger.warning("Work %d not found", work_id)
            return work
        except Exception as e:
            logger.error("Error getting work %d: %s", work_id, str(e))
            return None

    async def get_work_sentences(self, work_id: int) -> List[Sentence]:
        """Get all sentences for a work."""
        stmt = select(TextDivision).where(TextDivision.text_id == work_id)
        result = await self.session.execute(stmt)
        divisions = result.scalars().all()
        
        all_sentences = []
        for division in divisions:
            # Only get non-title lines
            stmt = select(TextLine).where(
                and_(
                    TextLine.division_id == division.id,
                    TextLine.line_number.isnot(None)  # Skip title lines
                )
            )
            result = await self.session.execute(stmt)
            db_lines = result.scalars().all()
            
            try:
                parser_lines = [
                    self._convert_to_parser_text_line(line, division)
                    for line in db_lines 
                    if line.content
                ]
                if parser_lines:
                    sentences = self.sentence_parser.parse_lines(parser_lines)
                    all_sentences.extend(sentences)
            except Exception as e:
                logger.error(f"Error parsing sentences in division {division.id}: {str(e)}")
                continue
            
        return all_sentences

    async def get_divisions(self, work_id: int) -> List[TextDivision]:
        """Get divisions for a work."""
        try:
            # Get divisions first
            result = await self.session.execute(
                select(TextDivision)
                .where(TextDivision.text_id == work_id)
            )
            divisions = result.scalars().all()
            
            if not divisions:
                logger.warning("No divisions found for work %d", work_id)
                return []
            
            # Get work structure using first division's info
            first_div = divisions[0]
            structure = self.citation_parser.get_work_structure(
                first_div.author_id_field,
                first_div.work_number_field
            )
            
            if structure:
                # Find parent of 'line' in structure
                structure_levels = [level.lower() for level in structure]
                try:
                    line_index = structure_levels.index('line')
                    if line_index > 0:  # If 'line' has a parent level
                        parent_level = structure_levels[line_index - 1]
                        # Map parent level to database field
                        db_field = map_level_to_field(parent_level, structure)
                        logger.debug(f"Using {db_field} for ordering based on parent of line in structure: {structure}")
                        # Sort divisions by the mapped field name
                        divisions.sort(key=lambda d: getattr(d, db_field) or "1")
                    else:
                        logger.debug("No parent level found for line, using first level for ordering")
                        first_level = structure[0].lower()
                        db_field = map_level_to_field(first_level, structure)
                        divisions.sort(key=lambda d: getattr(d, db_field) or "1")
                except ValueError:
                    logger.debug("'line' not found in structure, using first level for ordering")
                    first_level = structure[0].lower()
                    db_field = map_level_to_field(first_level, structure)
                    divisions.sort(key=lambda d: getattr(d, db_field) or "1")
            else:
                logger.debug("No work structure found, defaulting to chapter for ordering")
                divisions.sort(key=lambda d: d.chapter or "1")
            
            logger.debug("Found %d divisions for work %d", len(divisions), work_id)
            
            # Log division fields for debugging
            for division in divisions:
                logger.debug(f"Division fields: fragment={division.fragment}, volume={division.volume}, "
                           f"chapter={division.chapter}, section={division.section}, page={division.page}")
            
            return divisions
        except Exception as e:
            logger.error("Error getting divisions for work %d: %s", work_id, str(e))
            return []

    async def get_division_lines(self, division_id: int) -> List[TextLine]:
        """Get lines for a division."""
        try:
            # Get division first
            division_result = await self.session.execute(
                select(TextDivision).where(TextDivision.id == division_id)
            )
            division = division_result.scalar_one_or_none()
            if not division:
                logger.error("Division %d not found", division_id)
                return []

            # Get all lines in order, including titles
            result = await self.session.execute(
                select(TextLine)
                .where(TextLine.division_id == division_id)
                .order_by(TextLine.line_number)
            )
            
            lines = result.scalars().all()
            logger.debug("Found %d lines for division %d", len(lines), division_id)
            
            # Group lines by parent field value
            grouped_lines = {}
            for line in lines:
                parent_field, parent_value = self._get_parent_field(line)
                if parent_field and parent_value:
                    key = f"{parent_field}:{parent_value}"
                    if key not in grouped_lines:
                        grouped_lines[key] = []
                    grouped_lines[key].append(line)
                else:
                    # If no parent field found, use default group
                    if 'default' not in grouped_lines:
                        grouped_lines['default'] = []
                    grouped_lines['default'].append(line)
            
            # Sort lines within each group
            sorted_lines = []
            for group_key in sorted(grouped_lines.keys()):
                group = grouped_lines[group_key]
                # Sort by line number within group
                group.sort(key=lambda x: x.line_number if x.line_number is not None else float('inf'))
                sorted_lines.extend(group)
            
            # Add debug logging for each line's full content
            for line in sorted_lines:
                logger.debug("DB Line full content: '%s', is_title: %s", 
                           line.content, line.is_title)
            return sorted_lines
            
        except Exception as e:
            logger.error("Error getting lines for division %d: %s", division_id, str(e))
            return []

    async def get_sentence_analysis(self, sentence: Sentence) -> Dict[str, Any]:
        """Get NLP analysis for a sentence."""
        if not sentence.source_lines:
            return None
            
        line_content = sentence.source_lines[0].content
        
        stmt = select(TextLine).where(TextLine.content == line_content)
        result = await self.session.execute(stmt)
        line = result.scalar_one_or_none()
        
        if line:
            return line.spacy_tokens
        return None

    async def create_sentence_record(self, 
                                   sentence: Sentence, 
                                   processed_doc: Dict[str, Any],
                                   source_line_ids: List[int]) -> Sentence_Model:
        """Create a sentence record in the database."""
        # Create sentence record
        new_sentence = Sentence_Model(
            content=processed_doc["text"],
            source_line_ids=source_line_ids,
            start_position=0,
            end_position=len(processed_doc["text"]),
            spacy_data=processed_doc,
            # Get categories directly from token data
            categories=[token['category'] for token in processed_doc['tokens'] if token.get('category')]
        )
        
        self.session.add(new_sentence)
        await self.session.flush()
        return new_sentence

    async def update_line_analysis(self, 
                                 db_line: TextLine, 
                                 line_analysis: Dict[str, Any],
                                 sentence_id: int,
                                 first_token_pos: int,
                                 last_token_pos: int) -> None:
        """Update line analysis and create sentence association."""
        # Update line
        db_line.spacy_tokens = line_analysis
        # Get categories directly from token data
        db_line.categories = [token['category'] for token in line_analysis['tokens'] if token.get('category')]
        
        # Create association with sentence
        stmt = sentence_text_lines.insert().values(
            sentence_id=sentence_id,
            text_line_id=db_line.id,
            position_start=first_token_pos,
            position_end=last_token_pos
        )
        await self.session.execute(stmt)

    def reset(self):
        """Reset processor state."""
        super().reset()
        logger.debug("Reset CorpusDB state")
