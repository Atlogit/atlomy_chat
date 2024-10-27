"""
Migration script for citations to PostgreSQL database.

This script handles the migration of citations from text files to the new
PostgreSQL database schema, preserving citation components and relationships.
"""

import asyncio
import argparse
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from tqdm import tqdm

from toolkit.parsers.citation import CitationParser
from toolkit.migration.logging_config import setup_migration_logging, get_migration_logger
from toolkit.migration.content_validator import ContentValidator, ContentValidationError, DataVerifier
from toolkit.migration.citation_processor import CitationProcessor
from app.models.author import Author
from app.models.text import Text
from app.models.text_division import TextDivision
from app.models.text_line import TextLine

class MigrationError(Exception):
    """Custom exception for migration errors."""
    pass

class CitationMigrator:
    """Handles migration of citations to PostgreSQL database."""

    def __init__(self, session: AsyncSession):
        """Initialize the migrator with database session."""
        self.session = session
        self.citation_processor = CitationProcessor()
        self.data_verifier = DataVerifier(session)
        self.author_cache: Dict[str, int] = {}  # Cache author_id -> db_id
        self.text_cache: Dict[Tuple[str, str], int] = {}  # Cache (author_id, work_id) -> db_id
        self.division_line_counters: Dict[int, int] = {}  # Cache division_id -> current_line_number
        
        # Current state tracking for bracketed values
        self.current_values = {
            'author_id': None,
            'work_id': None,
            'division': None,
            'subdivision': None
        }
        
        # Batch processing settings
        self.batch_size = 100
        self.current_batch: List[Dict] = []
        
        # Load citation config
        with open('app/core/citation_config.json', 'r') as f:
            self.citation_config = json.load(f)
        
        # Set up logging
        setup_migration_logging()
        self.logger = get_migration_logger('citation_migrator')
        self.stats = {
            'processed_files': 0,
            'processed_citations': 0,
            'failed_citations': 0,
            'total_lines': 0,
            'validation_errors': 0
        }

    async def _get_or_create_author(self, author_id: str) -> int:
        """Get existing author or create new one."""
        if author_id in self.author_cache:
            return self.author_cache[author_id]
            
        # Check if author exists
        stmt = select(Author).where(Author.reference_code == author_id)
        result = await self.session.execute(stmt)
        author = result.scalar_one_or_none()
        
        if not author:
            # Create new author
            self.logger.debug(f"Creating new author with reference_code: {author_id}")
            author = Author(
                name=f"Author {author_id}",  # Set a default name
                reference_code=author_id,
                normalized_name=f"Author {author_id}"
            )
            self.session.add(author)
            await self.session.flush()
            
        self.author_cache[author_id] = author.id
        return author.id

    async def _get_or_create_text(self, author_id: str, work_id: str) -> int:
        """Get existing text or create new one."""
        cache_key = (author_id, work_id)
        if cache_key in self.text_cache:
            return self.text_cache[cache_key]
            
        # Check if text exists
        stmt = select(Text).where(
            Text.reference_code == work_id,
            Text.author_id == self.author_cache[author_id]
        )
        result = await self.session.execute(stmt)
        text = result.scalar_one_or_none()
        
        if not text:
            # Create new text
            self.logger.debug(f"Creating new text with reference_code: {work_id} for author: {author_id}")
            text = Text(
                author_id=self.author_cache[author_id],
                reference_code=work_id,
                title=f"Work {work_id}"  # Placeholder
            )
            self.session.add(text)
            await self.session.flush()
            
        self.text_cache[cache_key] = text.id
        return text.id

    async def _get_or_create_division(
        self,
        text_id: int,
        author_id: str,
        work_id: str,
        epithet: Optional[str] = None,
        fragment: Optional[str] = None,
        volume: Optional[str] = None,
        chapter: Optional[str] = None,
        section: Optional[str] = None,
        is_title: bool = False,
        title_number: Optional[str] = None
    ) -> int:
        """Get existing text division or create new one."""
        # Check if division exists with these components
        stmt = select(TextDivision).where(
            TextDivision.text_id == text_id,
            TextDivision.author_id_field == author_id,
            TextDivision.work_number_field == work_id,
            TextDivision.epithet_field == epithet,
            TextDivision.fragment_field == fragment,
            TextDivision.volume == volume,
            TextDivision.chapter == chapter,
            TextDivision.section == section,
            TextDivision.is_title == is_title,
            TextDivision.title_number == title_number
        )
        result = await self.session.execute(stmt)
        division_obj = result.scalar_one_or_none()
        
        if not division_obj:
            # Create new division with components
            self.logger.debug(
                f"Creating new text division for text {text_id} with "
                f"citation: [{author_id}] [{work_id}] [{epithet or ''}] [{fragment or ''}] "
                f"volume: {volume or ''}, chapter: {chapter or ''}, section: {section or ''}, "
                f"is_title: {is_title}, title_number: {title_number or ''}"
            )
            division_obj = TextDivision(
                text_id=text_id,
                author_id_field=author_id,
                work_number_field=work_id,
                epithet_field=epithet,
                fragment_field=fragment,
                volume=volume,
                chapter=chapter,
                section=section,
                is_title=is_title,
                title_number=title_number
            )
            self.session.add(division_obj)
            await self.session.flush()
            
            # Initialize line counter for new division
            self.division_line_counters[division_obj.id] = 1
            
        return division_obj.id

    async def _create_text_line(
        self,
        division_id: int,
        line_number: int,
        content: str,
        is_title: bool = False,
        script_type: Optional[str] = None
    ) -> None:
        """Create a new text line."""
        # Validate content before creating the line
        try:
            ContentValidator.validate(content)
            if script_type:
                ContentValidator.validate_script(content, script_type)
        except ContentValidationError as e:
            self.logger.error(f"Content validation failed: {str(e)}")
            self.stats['validation_errors'] += 1
            raise

        # For titles, use line number 0 or negative title number
        # For regular lines, use the current line counter if no specific line number given
        if is_title:
            final_line_number = line_number if line_number < 0 else 0
        else:
            if line_number == 0:  # No specific line number given
                final_line_number = self.division_line_counters.get(division_id, 1)
                self.division_line_counters[division_id] = final_line_number + 1
            else:
                final_line_number = line_number
                # Update counter to be one more than the highest line number seen
                self.division_line_counters[division_id] = max(
                    self.division_line_counters.get(division_id, 1),
                    line_number + 1
                )

        # Add to batch
        self.current_batch.append({
            'division_id': division_id,
            'line_number': final_line_number,
            'content': content,
            'categories': []
        })
        
        # Process batch if full
        if len(self.current_batch) >= self.batch_size:
            await self._process_batch()

        self.stats['processed_citations'] += 1

    async def _process_batch(self) -> None:
        """Process a batch of text lines."""
        if not self.current_batch:
            return

        # Create all lines in batch
        text_lines = [TextLine(**line_data) for line_data in self.current_batch]
        self.session.add_all(text_lines)
        await self.session.flush()
        
        # Clear batch
        self.current_batch = []

    async def migrate_section(self, citation: str, text: str, script_type: Optional[str] = None) -> None:
        """Migrate a section of text with its citation information."""
        try:
            # Extract citation values
            new_values = self.citation_processor.extract_bracketed_values(citation)
            
            # Update current values with any new values
            self.current_values.update(new_values)
            
            # Skip processing if we don't have required values
            if not self.current_values['author_id'] or not self.current_values['work_id']:
                self.logger.debug("Skipping section - missing required author_id or work_id")
                return
            
            # Create author and text entries
            author_db_id = await self._get_or_create_author(self.current_values['author_id'])
            text_db_id = await self._get_or_create_text(
                self.current_values['author_id'],
                self.current_values['work_id']
            )
            
            # Process each line in the section
            lines = text.strip().split('\n')
            for line in lines:
                if not line.strip():
                    continue
                    
                content, is_title, line_number, section = self.citation_processor.extract_line_info(line)
                if not content:  # Skip lines with no content
                    continue
                
                # Create or get division with metadata
                division_db_id = await self._get_or_create_division(
                    text_db_id,
                    author_id=self.current_values['author_id'],
                    work_id=self.current_values['work_id'],
                    epithet=self.current_values['division'],
                    fragment=self.current_values['subdivision'],
                    section=section,  # Use section from line info
                    is_title=is_title,
                    title_number=str(abs(line_number)) if is_title and line_number else None
                )
                
                # Create text line
                await self._create_text_line(division_db_id, line_number, content, is_title, script_type)
                
        except Exception as e:
            self.logger.error(f"Error migrating section with citation {citation}: {str(e)}")
            self.stats['failed_citations'] += 1
            raise

    async def process_text_file(self, file_path: Path, script_type: Optional[str] = None) -> None:
        """Process a text file and migrate its citations."""
        try:
            self.logger.info(f"Processing file: {file_path}")
            
            # Reset current values for new file
            self.current_values = {
                'author_id': None,
                'work_id': None,
                'division': None,
                'subdivision': None
            }
            
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
                
            # Split text into sections
            sections = self.citation_processor.split_sections(text)
            
            # Process each section
            self.stats['total_lines'] = sum(len(s.strip().split('\n')) for s in sections[1::2])
            
            for i in range(1, len(sections), 2):
                citation = sections[i].strip()
                section_text = sections[i+1].strip() if i+1 < len(sections) else ""
                await self.migrate_section(citation, section_text, script_type)
            
            # Process any remaining batch items
            await self._process_batch()
                        
            self.stats['processed_files'] += 1
            
            # Log statistics for this file
            self.logger.info(f"File processing completed: {file_path}")
            self.logger.info(f"Lines processed: {self.stats['total_lines']}")
            self.logger.info(f"Citations processed: {self.stats['processed_citations']}")
            self.logger.info(f"Failed citations: {self.stats['failed_citations']}")
            self.logger.info(f"Validation errors: {self.stats['validation_errors']}")
            
        except Exception as e:
            self.logger.error(f"Error processing file {file_path}: {str(e)}")
            raise

    async def verify_migration(self) -> Dict:
        """Run post-migration verification."""
        self.logger.info("Running post-migration verification...")
        verification_results = await self.data_verifier.run_all_verifications()
        
        # Log verification results
        if verification_results['relationship_errors']:
            self.logger.error("Found relationship errors:")
            for error in verification_results['relationship_errors']:
                self.logger.error(f"  - {error}")
                
        if verification_results['content_integrity_issues']:
            self.logger.error("Found content integrity issues:")
            for issue in verification_results['content_integrity_issues']:
                self.logger.error(f"  - {issue}")
                
        if verification_results['line_continuity_issues']:
            self.logger.error("Found line continuity issues:")
            for issue in verification_results['line_continuity_issues']:
                self.logger.error(f"  - Division {issue['division_id']}: "
                             f"Expected line {issue['expected']}, found {issue['found']}")
                
        if verification_results['incomplete_texts']:
            self.logger.error("Found incomplete texts:")
            for text in verification_results['incomplete_texts']:
                self.logger.error(f"  - Text {text['text_id']}: {text['issue']}")
        
        return verification_results

    async def migrate_directory(self, directory: Path, script_type: Optional[str] = None) -> None:
        """Migrate all text files in a directory."""
        try:
            self.logger.info(f"Starting migration of directory: {directory}")
            
            # Get list of text files
            text_files = list(directory.glob('**/*.txt'))
            self.logger.info(f"Found {len(text_files)} text files to process")
            
            # Process each file
            for file_path in tqdm(text_files, desc="Processing files", unit="file"):
                await self.process_text_file(file_path, script_type)
                await self.session.commit()
            
            # Run verification
            verification_results = await self.verify_migration()
            
            # If there are serious issues, raise exception
            if any(verification_results.values()):
                raise MigrationError("Post-migration verification failed. Check logs for details.")
                
            # Log final statistics
            self.logger.info("Migration completed successfully")
            self.logger.info(f"Files processed: {self.stats['processed_files']}")
            self.logger.info(f"Total lines processed: {self.stats['total_lines']}")
            self.logger.info(f"Citations processed: {self.stats['processed_citations']}")
            self.logger.info(f"Failed citations: {self.stats['failed_citations']}")
                
        except Exception as e:
            self.logger.error(f"Error migrating directory {directory}: {str(e)}")
            await self.session.rollback()
            raise
        finally:
            await self.session.close()

async def main():
    """Main migration function."""
    parser = argparse.ArgumentParser(description='Migrate citations to PostgreSQL database')
    parser.add_argument('--file', type=str, help='Single file to process')
    parser.add_argument('--dir', type=str, help='Directory containing text files to process')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    args = parser.parse_args()

    if args.debug:
        logging.getLogger('citation_migrator').setLevel(logging.DEBUG)

    from app.core.database import async_session
    
    async with async_session() as session:
        migrator = CitationMigrator(session)
        
        if args.file:
            file_path = Path(args.file)
            if not file_path.exists():
                print(f"Error: File not found: {file_path}")
                return
            await migrator.process_text_file(file_path)
            await session.commit()
        elif args.dir:
            directory = Path(args.dir)
            if not directory.exists():
                print(f"Error: Directory not found: {directory}")
                return
            await migrator.migrate_directory(directory)
        else:
            print("Error: Please specify either --file or --dir")

if __name__ == "__main__":
    asyncio.run(main())
