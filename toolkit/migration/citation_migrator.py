"""
Migration script for citations to PostgreSQL database.

This script handles the migration of citations from text files to the new
PostgreSQL database schema, preserving citation components and relationships.
"""

import asyncio
import argparse
import json
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from tqdm import tqdm

from toolkit.parsers.citation import CitationParser, Citation
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
        
        # Set up logging
        setup_migration_logging()
        self.logger = get_migration_logger('citation_migrator')
        self.stats = {
            'processed_files': 0,
            'processed_lines': 0,
            'failed_citations': 0,
            'validation_errors': 0
        }

    def _normalize_reference_code(self, ref_code: str) -> str:
        """Normalize reference codes to prevent duplicates."""
        # Remove 'TLG' prefix if present
        if ref_code.startswith('TLG'):
            ref_code = ref_code[3:]
        return ref_code

    def _extract_work_id(self, filename: str) -> Optional[str]:
        """Extract work ID from filename."""
        # Try to extract work number from patterns like:
        # TLG0627_hippocrates-050.txt or TLG0057_galen-001.txt
        match = re.search(r'-(\d+)(?:\.txt)?$', filename)
        if match:
            return match.group(1)
        return None

    async def _get_or_create_author(self, author_id: str) -> int:
        """Get existing author or create new one."""
        normalized_id = self._normalize_reference_code(author_id)
        
        if normalized_id in self.author_cache:
            return self.author_cache[normalized_id]
            
        # Check if author exists with normalized reference code
        stmt = select(Author).where(Author.reference_code == normalized_id)
        result = await self.session.execute(stmt)
        author = result.scalar_one_or_none()
        
        if not author:
            # Create new author with normalized reference code
            self.logger.debug(f"Creating new author with reference_code: {normalized_id}")
            author = Author(
                name=f"Author {normalized_id}",
                reference_code=normalized_id,
                normalized_name=f"Author {normalized_id}"
            )
            self.session.add(author)
            await self.session.flush()
            
        self.author_cache[normalized_id] = author.id
        return author.id

    async def _get_or_create_text(self, author_id: str, work_id: str) -> int:
        """Get existing text or create new one."""
        normalized_author_id = self._normalize_reference_code(author_id)
        cache_key = (normalized_author_id, work_id)
        
        if cache_key in self.text_cache:
            return self.text_cache[cache_key]
            
        # Check if text exists
        stmt = select(Text).where(
            Text.reference_code == work_id,
            Text.author_id == self.author_cache[normalized_author_id]
        )
        result = await self.session.execute(stmt)
        text = result.scalar_one_or_none()
        
        if not text:
            # Create new text
            self.logger.debug(f"Creating new text with reference_code: {work_id} for author: {normalized_author_id}")
            text = Text(
                author_id=self.author_cache[normalized_author_id],
                reference_code=work_id,
                title=f"Work {work_id}"
            )
            self.session.add(text)
            await self.session.flush()
            
        self.text_cache[cache_key] = text.id
        return text.id

    async def process_text_file(self, file_path: Path, script_type: Optional[str] = None) -> None:
        """Process a text file and migrate its citations."""
        try:
            self.logger.info(f"Processing file: {file_path}")
            
            # Extract author and work IDs from filename
            filename = file_path.stem
            author_match = re.match(r'(?:TLG)?(\d+).*', filename)
            file_author_id = author_match.group(1) if author_match else None
            file_work_id = self._extract_work_id(filename)
            
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
                
            # Process text into sections
            sections = self.citation_processor.process_text(text)
            
            # Organize sections into divisions
            divisions = []
            current_division = None
            current_tlg = None
            text_db_id = None
            
            # First pass - collect divisions and lines
            for section in sections:
                line_citation = section['citation']
                inherited_citation = section['inherited_citation']
                content = section['content']
                
                # Skip empty sections
                if not content:
                    continue
                    
                # Update current TLG citation if we have one
                if inherited_citation and inherited_citation.author_id:
                    current_tlg = inherited_citation
                    # Create author and text when we first get TLG citation
                    if not text_db_id:
                        author_db_id = await self._get_or_create_author(inherited_citation.author_id)
                        text_db_id = await self._get_or_create_text(
                            inherited_citation.author_id,
                            inherited_citation.work_id
                        )
                
                # If we don't have a text_db_id yet, try to use filename info
                if not text_db_id and file_author_id and file_work_id:
                    author_db_id = await self._get_or_create_author(file_author_id)
                    text_db_id = await self._get_or_create_text(file_author_id, file_work_id)
                    self.logger.info(f"Created text from filename: author={file_author_id}, work={file_work_id}")
                
                # Skip if we still can't determine the text
                if not text_db_id:
                    self.logger.warning("Skipping section - could not determine text ID")
                    continue
                
                # Get chapter from line citation
                chapter = line_citation.chapter if line_citation else None
                
                # Create new division if needed
                if not current_division or (chapter and chapter != current_division.get("chapter")):
                    current_division = {
                        "author_id_field": current_tlg.author_id if current_tlg else file_author_id,
                        "work_number_field": current_tlg.work_id if current_tlg else file_work_id,
                        "epithet_field": None,
                        "fragment_field": None,
                        "volume": None,
                        "chapter": chapter or "1",  # Use default chapter if none provided
                        "section": None,
                        "lines": []
                    }
                    divisions.append(current_division)
                    self.logger.debug(f"Created new division: {current_division}")
                
                # Add line to current division
                if line_citation and line_citation.line:
                    line_number = int(line_citation.line)
                else:
                    # Use sequential numbering if no line number provided
                    line_number = len(current_division["lines"]) + 1
                
                line_data = {
                    "line_number": line_number,
                    "content": content
                }
                current_division["lines"].append(line_data)
                self.logger.debug(f"Added line to division: {line_data}")
                self.stats['processed_lines'] += 1
            
            # Create at least one division if none exist
            if not divisions and text_db_id:
                divisions = [{
                    "author_id_field": current_tlg.author_id if current_tlg else file_author_id,
                    "work_number_field": current_tlg.work_id if current_tlg else file_work_id,
                    "epithet_field": None,
                    "fragment_field": None,
                    "volume": None,
                    "chapter": "1",  # Default chapter
                    "section": None,
                    "lines": []
                }]
            
            # Second pass - create divisions and lines in database
            if divisions and text_db_id:
                self.logger.info(f"Creating {len(divisions)} divisions with {self.stats['processed_lines']} lines")
                
                # Create all divisions first
                division_objects = []
                for division in divisions:
                    # Normalize author_id_field
                    if division["author_id_field"]:
                        division["author_id_field"] = self._normalize_reference_code(division["author_id_field"])
                        
                    division_obj = TextDivision(
                        text_id=text_db_id,
                        author_id_field=division["author_id_field"],
                        work_number_field=division["work_number_field"],
                        epithet_field=division["epithet_field"],
                        fragment_field=division["fragment_field"],
                        volume=division["volume"],
                        chapter=division["chapter"],
                        section=division["section"]
                    )
                    self.session.add(division_obj)
                    division_objects.append((division_obj, division["lines"]))
                
                # Flush to get division IDs
                await self.session.flush()
                self.logger.debug("Created divisions in database")
                
                # Create lines for each division
                for division_obj, lines in division_objects:
                    # Sort lines by line number to ensure proper order
                    sorted_lines = sorted(lines, key=lambda x: x["line_number"])
                    
                    # Normalize line numbers to be sequential
                    normalized_lines = []
                    for i, line in enumerate(sorted_lines, 1):
                        normalized_lines.append(
                            TextLine(
                                division_id=division_obj.id,
                                line_number=i,
                                content=line["content"]
                            )
                        )
                    
                    self.session.add_all(normalized_lines)
                    self.logger.debug(f"Adding {len(normalized_lines)} lines for division {division_obj.id}")
                
                # Flush all lines
                await self.session.flush()
                self.logger.debug("Flushed all lines to database")
                
                # Verify lines were created
                for division_obj, _ in division_objects:
                    result = await self.session.execute(
                        select(TextLine).filter_by(division_id=division_obj.id)
                    )
                    lines = result.scalars().all()
                    count = len(lines)
                    self.logger.debug(f"Division {division_obj.id} has {count} lines")
                    if count == 0:
                        self.logger.error(f"No lines found for division {division_obj.id}")
                
                # Final commit
                await self.session.commit()
                self.logger.debug("Committed all changes to database")
            
            self.stats['processed_files'] += 1
            
            # Log statistics for this file
            self.logger.info(f"File processing completed: {file_path}")
            self.logger.info(f"Lines processed: {self.stats['processed_lines']}")
            self.logger.info(f"Failed citations: {self.stats['failed_citations']}")
            self.logger.info(f"Validation errors: {self.stats['validation_errors']}")
            
        except Exception as e:
            self.logger.error(f"Error processing file {file_path}: {str(e)}")
            await self.session.rollback()
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
            
            # Get list of text files, excluding pipeline reports
            text_files = [
                f for f in directory.glob('**/*.txt')
                if 'pipeline_reports' not in str(f)
            ]
            self.logger.info(f"Found {len(text_files)} text files to process")
            
            # Process each file
            for file_path in tqdm(text_files, desc="Processing files", unit="file"):
                await self.process_text_file(file_path, script_type)
            
            # Run verification
            verification_results = await self.verify_migration()
            
            # If there are serious issues, raise exception
            if any(verification_results.values()):
                raise MigrationError("Post-migration verification failed. Check logs for details.")
                
            # Log final statistics
            self.logger.info("Migration completed successfully")
            self.logger.info(f"Files processed: {self.stats['processed_files']}")
            self.logger.info(f"Total lines processed: {self.stats['processed_lines']}")
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
