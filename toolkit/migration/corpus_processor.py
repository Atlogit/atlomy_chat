"""
Main corpus processor for text analysis.

Coordinates specialized processors for line processing,
sentence formation, and database operations.
"""

from typing import Optional, Dict, Any, List
from tqdm import tqdm

from .corpus_db import CorpusDB
from toolkit.parsers.citation import CitationParser
from toolkit.parsers.citation_utils import map_level_to_field

# Import migration logging configuration
from toolkit.migration.logging_config import get_migration_logger

# Use migration logger instead of standard logger
logger = get_migration_logger('migration.corpus_processor')

class CorpusProcessor(CorpusDB):
    """Main coordinator for corpus processing."""

    def __init__(self, session: Any, model_path: Optional[str] = None, use_gpu: Optional[bool] = None, report: Optional[Any] = None, skip_nlp: bool = False):
        """Initialize the corpus processor.
        
        Args:
            session: SQLAlchemy async session
            model_path: Optional path to spaCy model
            use_gpu: Whether to use GPU for NLP processing (None for auto-detect)
            report: Optional PipelineReport for tracking issues
            skip_nlp: Whether to skip NLP token generation
        """
        super().__init__(session, model_path=model_path, use_gpu=use_gpu)
        self._current_metadata = None  # Track current metadata
        self.report = report  # Store report for tracking issues
        self.skip_nlp = skip_nlp  # Flag to skip NLP processing
        
        # Set report in citation parser
        if report:
            CitationParser.get_instance().set_report(report)
            
        logger.info(f"CorpusProcessor initialized (Skip NLP: {self.skip_nlp})")


    def _set_metadata(self, metadata: Optional[Dict[str, str]]) -> None:
        """Set current metadata context."""
        self._current_metadata = metadata
        if metadata:
            logger.debug("Set current metadata context: author_id=%s, work_id=%s", 
                        metadata.get('author_id'), metadata.get('work_id'))
        else:
            logger.debug("Cleared metadata context")

    def _get_division_field_value(self, division) -> tuple[str, str]:
        """Get the appropriate field and value based on work structure.
        Uses the parent field of 'line' from the work structure."""
        try:
            # Get work structure
            structure = self.citation_parser.get_work_structure(
                division.author_id_field,
                division.work_number_field
            )
            
            if structure:
                # Convert structure to lowercase for consistent comparison
                structure_levels = [level.lower() for level in structure]
                logger.debug(f"Found work structure: {structure_levels}")
                
                # Find 'line' in structure and get its parent
                try:
                    line_index = structure_levels.index('line')
                    if line_index > 0:  # If 'line' has a parent level
                        parent_level = structure_levels[line_index - 1]
                        logger.debug(f"Found parent level of line: {parent_level}")
                        
                        # Map the parent level to a database field
                        db_field = map_level_to_field(parent_level, structure)
                        logger.debug(f"Mapped {parent_level} to database field {db_field}")
                        
                        # Get value for the parent field
                        value = getattr(division, db_field)
                        if value is not None:
                            logger.debug(f"Using {db_field} value: {value}")
                            return db_field, value
                        else:
                            logger.debug(f"No value found for {db_field}, using default '1'")
                            return db_field, "1"
                except ValueError:
                    logger.debug("'line' not found in structure")
            
            # If no structure or no line field found, try common fields in order
            for field in ['page', 'chapter', 'section', 'book', 'volume']:
                value = getattr(division, field)
                if value is not None:
                    logger.debug(f"Using {field} value: {value}")
                    return field, value
            
            # If no valid field found, default to chapter "1"
            logger.debug("No valid division field found, defaulting to chapter 1")
            return 'chapter', "1"
            
        except Exception as e:
            logger.error(f"Error getting division field value: {str(e)}")
            # Default to chapter "1" on error
            return 'chapter', "1"

    async def process_work(self, work_id: int, pbar: Optional[tqdm] = None) -> None:
        """Process all text in a work through the NLP pipeline."""
        try:
            # Get work details
            work = await self.get_work(work_id)
            if not work:
                logger.error("Could not find work with ID %d", work_id)
                if self.report:
                    self.report.add_sentence_issue(f"work_{work_id}", "Work not found")
                return
                
            # Get divisions
            divisions = await self.get_divisions(work_id)
            if not divisions:
                logger.warning("No divisions found for work %d", work_id)
                if self.report:
                    self.report.add_sentence_issue(f"work_{work_id}", "No divisions found")
                return
            
            # Only clear metadata context, don't reset everything
            self._set_metadata(None)
            
            async with self.session.begin_nested():
                for division in divisions:
                    try:
                        # Get appropriate field and value based on work structure
                        field_name, field_value = self._get_division_field_value(division)
                        logger.info("Processing division %d (%s %s)", 
                                  division.id, field_name, field_value)
                        
                        # Get lines
                        db_lines = await self.get_division_lines(division.id)
                        if not db_lines:
                            logger.warning("No lines found in division %d", division.id)
                            if self.report:
                                self.report.add_sentence_issue(f"division_{division.id}", "No lines found")
                            continue
                        
                        # Convert lines to parser format
                        parser_lines = self.process_lines(db_lines, division)
                        if not parser_lines:
                            logger.warning("No parser lines created for division %d", division.id)
                            if self.report:
                                self.report.add_sentence_issue(f"division_{division.id}", "No parser lines created")
                            continue
                        
                        # Check first line for metadata but keep it in parser_lines
                        if parser_lines and hasattr(parser_lines[0], 'is_metadata') and parser_lines[0].is_metadata:
                            self._set_metadata(parser_lines[0].metadata)
                        
                        # Parse sentences
                        sentences = self.parse_sentences(parser_lines)
                        if not sentences:
                            logger.warning("No sentences parsed from division %d", division.id)
                            if self.report:
                                self.report.add_sentence_issue(f"division_{division.id}", "No sentences parsed")
                            continue
                        
                        # Process each sentence
                        for sentence in sentences:
                            try:
                                # Conditionally process through NLP
                                processed_doc = None
                                if not self.skip_nlp:
                                    processed_doc = self.process_sentence(sentence)
                                    if not processed_doc:
                                        if self.report:
                                            self.report.add_nlp_issue(f"division_{division.id}", "NLP processing failed")
                                        continue
                                
                                # Get database lines for sentence
                                sentence_lines = self.get_sentence_lines(sentence, db_lines)
                                if not sentence_lines:
                                    logger.warning("No database lines found for sentence: %s", 
                                                sentence.content)
                                    logger.debug("Source lines had line numbers: %s",
                                            [str(self._get_line_number(line)) 
                                                for line in sentence.source_lines])
                                    if self.report:
                                        self.report.add_sentence_issue(f"division_{division.id}", "No database lines found for sentence")
                                    continue
                                    
                                # Create mapping of line numbers to line IDs
                                line_map = {}
                                for line in db_lines:
                                    line_num = self._get_line_number(line)
                                    if line_num is not None:
                                        line_map[line_num] = line.id
                                
                                # Get source line IDs in order
                                source_line_ids = []
                                for line in sentence.source_lines:
                                    line_num = self._get_line_number(line)
                                    if line_num is not None and line_num in line_map:
                                        source_line_ids.append(line_map[line_num])

                                # Create sentence record
                                new_sentence = await self.create_sentence_record(
                                    sentence, 
                                    processed_doc,  # This will be None if skip_nlp is True
                                    source_line_ids
                                )
                                if not new_sentence:
                                    if self.report:
                                        self.report.add_sentence_issue(f"division_{division.id}", "Failed to create sentence record")
                                    continue

                                # Update line analysis only if NLP processing was done
                                if processed_doc and processed_doc['tokens']:
                                    for db_line in sentence_lines:
                                        line_analysis = self._map_tokens_to_line(
                                            db_line.content,
                                            processed_doc
                                        )
                                        
                                        if line_analysis:
                                            first_token_pos = db_line.content.find(
                                                line_analysis['tokens'][0]['text']
                                            )
                                            last_token_pos = (
                                                db_line.content.rfind(line_analysis['tokens'][-1]['text']) + 
                                                len(line_analysis['tokens'][-1]['text'])
                                            )
                                            
                                            await self.update_line_analysis(
                                                db_line,
                                                line_analysis,
                                                new_sentence.id,
                                                first_token_pos,
                                                last_token_pos
                                            )
                                                
                                        await self.session.flush()
                                    
                            except Exception as e:
                                logger.error("Error processing sentence in division %d: %s", 
                                           division.id, str(e))
                                if self.report:
                                    self.report.add_sentence_issue(f"division_{division.id}", f"Error processing sentence: {str(e)}")
                                continue
                        
                        if pbar:
                            pbar.update(1)
                            pbar.set_description(f"Processing work {work_id}")

                    except Exception as e:
                        logger.error("Error processing division %d: %s", division.id, str(e))
                        if self.report:
                            self.report.add_sentence_issue(f"division_{division.id}", f"Error processing division: {str(e)}")
                        continue

        except Exception as e:
            logger.error("Error processing work %d: %s", work_id, str(e))
            if self.report:
                self.report.add_sentence_issue(f"work_{work_id}", f"Error processing work: {str(e)}")

    async def process_corpus(self) -> None:
        """Process all works in the corpus."""
        # Get all works
        works = await self.get_work_list()
        if not works:
            logger.error("No works found in corpus")
            if self.report:
                self.report.add_sentence_issue("corpus", "No works found")
            return
            
        total_works = len(works)
        logger.info("Starting sequential processing of %d works", total_works)
        
        # Process each work
        with tqdm(total=total_works, desc="Processing corpus", unit="work") as pbar:
            for work in works:
                try:
                    await self.process_work(work.id, pbar)
                    await self.session.commit()
                    logger.info("Committed changes for work %d", work.id)
                except Exception as e:
                    logger.error("Error processing work %d: %s", work.id, str(e))
                    if self.report:
                        self.report.add_sentence_issue(f"work_{work.id}", f"Failed to process work: {str(e)}")
                    await self.session.rollback()
                    logger.info("Rolled back changes for work %d", work.id)
                    continue

    def reset(self):
        """Reset processor state."""
        self._set_metadata(None)
        logger.debug("Reset CorpusProcessor state")
