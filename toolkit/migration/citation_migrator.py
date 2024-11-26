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
import sys
import traceback

from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine, create_async_engine
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError, OperationalError, DatabaseError
from sqlalchemy.orm.exc import NoResultFound
from tqdm import tqdm

from toolkit.parsers.shared_parsers import SharedParsers
from toolkit.migration.logging_config import setup_migration_logging, get_migration_logger
from toolkit.migration.content_validator import ContentValidator, ContentValidationError, DataVerifier
from toolkit.migration.citation_processor import CitationProcessor
from app.models.author import Author
from app.models.text import Text
from app.models.text_division import TextDivision
from app.models.text_line import TextLine
from assets.indexes import tlg_index, work_numbers
from toolkit.parsers.citation_utils import map_level_to_field
from app.core.config import settings

class UnicodeLoggingHandler(logging.StreamHandler):
    """Custom logging handler to handle Unicode characters."""
    def emit(self, record):
        try:
            msg = self.format(record)
            # Encode with UTF-8, replacing problematic characters
            stream = self.stream
            stream.write(msg.encode('utf-8', errors='replace').decode('utf-8') + self.terminator)
            self.flush()
        except Exception:
            self.handleError(record)

class MigrationError(Exception):
    """Custom exception for migration errors."""
    pass

class CitationMigrator:
    """Handles migration of citations to PostgreSQL database."""

    def __init__(self, session: AsyncSession, engine: Optional[AsyncEngine] = None):
        """Initialize the migrator with database session and optional engine."""
        self.session = session
        self.engine = engine
        self.citation_processor = CitationProcessor()
        # Get shared parser components
        shared = SharedParsers.get_instance()
        self.citation_parser = shared.citation_parser
        self.data_verifier = DataVerifier(session)
        self.author_cache: Dict[str, int] = {}  # Cache author_id -> db_id
        self.text_cache: Dict[Tuple[str, str], int] = {}  # Cache (author_id, work_id) -> db_id
        
        # Set up logging
        setup_migration_logging()
        self.logger = get_migration_logger('citation_migrator')
        
        # Add Unicode-safe handler
        unicode_handler = UnicodeLoggingHandler()
        unicode_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(unicode_handler)
        
        self.stats = {
            'processed_files': 0,
            'processed_lines': 0,
            'failed_citations': 0,
            'validation_errors': 0,
            'divisions_created': 0,
            'lines_per_division': {}, 
            'failed_files': []  # Track files that failed to process
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

    def _clean_line_number(self, line_number: Optional[str]) -> Optional[str]:
        """Clean line number by removing any content after tab."""
        if not line_number:
            return None
        # Split on tab and take first part
        return line_number.split('\t')[0] if '\t' in line_number else line_number

    async def _get_or_create_text(self, author_id: str, work_id: str) -> int:
        """Get existing text or create new one with advanced error handling."""
        max_retries = 5
        retry_delay = 1  # Initial delay in seconds
        
        for attempt in range(max_retries):
            try:
                # Normalize and validate inputs
                normalized_author_id = self._normalize_reference_code(author_id)
                
                # Validate work_id
                if not work_id or not isinstance(work_id, str):
                    raise ValueError(f"Invalid work_id: {work_id}")
                
                # Check cache first
                cache_key = (normalized_author_id, work_id)
                if cache_key in self.text_cache:
                    return self.text_cache[cache_key]
                
                # Ensure author exists in cache
                if normalized_author_id not in self.author_cache:
                    # Create or retrieve author if not in cache
                    author_db_id = await self._get_or_create_author(normalized_author_id)
                    self.author_cache[normalized_author_id] = author_db_id
                
                # Query for existing text
                stmt = select(Text).where(
                    Text.reference_code == work_id,
                    Text.author_id == self.author_cache[normalized_author_id]
                )
                
                # Execute query with timeout
                result = await asyncio.wait_for(
                    self.session.execute(stmt), 
                    timeout=10.0  # 10-second timeout
                )
                text = result.scalar_one_or_none()
                
                # Create new text if not found
                if not text:
                    text = Text(
                        author_id=self.author_cache[normalized_author_id],
                        reference_code=work_id,
                        title=f"Work {work_id}"
                    )
                    self.session.add(text)
                    await self.session.flush()
                
                # Cache and return text ID
                self.text_cache[cache_key] = text.id
                return text.id
            
            except (OperationalError, NoResultFound, asyncio.TimeoutError) as e:
                # Log specific error details
                self.logger.warning(
                    f"Database error on attempt {attempt + 1}: {type(e).__name__} - {str(e)}"
                )
                
                # Exponential backoff
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay * (2 ** attempt))
                    
                    # Attempt to reset session
                    try:
                        await self._reset_session()
                    except Exception as reset_error:
                        self.logger.error(f"Session reset failed: {str(reset_error)}")
                else:
                    # Final error handling
                    self.logger.error(
                        f"Failed to get or create text after {max_retries} attempts. "
                        f"Author ID: {normalized_author_id}, Work ID: {work_id}"
                    )
                    raise MigrationError(f"Persistent database error: {str(e)}")
            
            except Exception as unexpected_error:
                # Catch-all for unexpected errors
                self.logger.error(
                    f"Unexpected error in text creation: {type(unexpected_error).__name__} - {str(unexpected_error)}"
                )
                raise

    async def _get_or_create_author(self, author_id: str) -> int:
        """Get existing author or create new one."""
        try:
            normalized_id = self._normalize_reference_code(author_id)
            
            if normalized_id in self.author_cache:
                return self.author_cache[normalized_id]
                
            # Check if author exists with normalized reference code
            stmt = select(Author).where(Author.reference_code == normalized_id)
            result = await self.session.execute(stmt)
            author = result.scalar_one_or_none()
            
            if not author:
                # Create new author with normalized reference code
                author = Author(
                    name=f"Author {normalized_id}",
                    reference_code=normalized_id,
                    normalized_name=f"Author {normalized_id}"
                )
                self.session.add(author)
                await self.session.flush()
                
            self.author_cache[normalized_id] = author.id
            return author.id
        except Exception as e:
            self.logger.error(f"Error creating author: {str(e)}")
            raise

    async def _get_or_create_text(self, author_id: str, work_id: str) -> int:
        """Get existing text or create new one."""
        try:
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
                text = Text(
                    author_id=self.author_cache[normalized_author_id],
                    reference_code=work_id,
                    title=f"Work {work_id}"
                )
                self.session.add(text)
                await self.session.flush()
                
            self.text_cache[cache_key] = text.id
            return text.id
        except Exception as e:
            self.logger.error(f"Error creating text: {str(e)}")
            raise

    def _get_division_key_and_field(self, citation, inherited_citation) -> Tuple[str, str]:
        """Generate a unique key for a division and determine which field it belongs in.
        Uses the parent field of 'line' from the work structure."""
        # Try to get work structure from citation
        structure = None
        if citation and citation.author_id and citation.work_id:
            structure = self.citation_parser.get_work_structure(citation.author_id, citation.work_id)
            if structure:
                self.logger.debug(f"Found work structure for {citation.author_id}.{citation.work_id}: {structure}")
        elif inherited_citation and inherited_citation.author_id and inherited_citation.work_id:
            structure = self.citation_parser.get_work_structure(inherited_citation.author_id, inherited_citation.work_id)
            if structure:
                self.logger.debug(f"Found work structure for {inherited_citation.author_id}.{inherited_citation.work_id}: {structure}")

        if structure:
            # Convert structure to lowercase for consistent comparison
            structure_levels = [level.lower() for level in structure]
            self.logger.debug(f"Structure levels: {structure_levels}")
            
            # Find 'line' in structure and get its parent
            try:
                line_index = structure_levels.index('line')
                if line_index > 0:  # If 'line' has a parent level
                    parent_level = structure_levels[line_index - 1]
                    self.logger.debug(f"Found parent level of line: {parent_level}")
                    
                    # Map the parent level to a database field
                    db_field = map_level_to_field(parent_level, structure)
                    self.logger.debug(f"Mapped {parent_level} to database field {db_field}")
                    
                    # Get the value from the appropriate citation using the mapped field name
                    if citation and citation.hierarchy_levels and db_field in citation.hierarchy_levels:
                        value = citation.hierarchy_levels[db_field]
                        # Strip any content after tab character
                        if isinstance(value, str) and '\t' in value:
                            value = value.split('\t')[0]
                        self.logger.debug(f"Using value '{value}' from citation hierarchy_levels[{db_field}]")
                        return value, db_field
                    elif inherited_citation and inherited_citation.hierarchy_levels and db_field in inherited_citation.hierarchy_levels:
                        value = inherited_citation.hierarchy_levels[db_field]
                        # Strip any content after tab character
                        if isinstance(value, str) and '\t' in value:
                            value = value.split('\t')[0]
                        self.logger.debug(f"Using value '{value}' from inherited_citation hierarchy_levels[{db_field}]")
                        return value, db_field
                    
                    # If no value found but we have parent field, use "1"
                    self.logger.debug(f"No value found in hierarchy_levels, using default '1' with field {db_field}")
                    return "1", db_field
                else:
                    self.logger.debug("'line' found but has no parent level")
            except ValueError:
                self.logger.debug("'line' not found in structure")
            
            # If no line field or no parent, try common fields in order
            for field in ['page', 'chapter', 'section', 'book', 'volume']:
                # Try citation first
                if citation and citation.hierarchy_levels and field in citation.hierarchy_levels:
                    value = citation.hierarchy_levels[field]
                    if isinstance(value, str) and '\t' in value:
                        value = value.split('\t')[0]
                    return value, field
                # Then try inherited citation
                elif inherited_citation and inherited_citation.hierarchy_levels and field in inherited_citation.hierarchy_levels:
                    value = inherited_citation.hierarchy_levels[field]
                    if isinstance(value, str) and '\t' in value:
                        value = value.split('\t')[0]
                    return value, field
            
            # If still no value found, use first level from structure
            first_level = structure[0].lower()
            db_field = map_level_to_field(first_level, structure)
            self.logger.debug(f"Using first level {first_level} as fallback")
            return "1", db_field

        # No structure found, use chapter as fallback
        self.logger.debug("No work structure found, using chapter as fallback")
        if citation and citation.chapter:
            value = citation.chapter
            # Strip any content after tab character
            if isinstance(value, str) and '\t' in value:
                value = value.split('\t')[0]
            return value, 'chapter'
        elif inherited_citation and inherited_citation.chapter:
            value = inherited_citation.chapter
            # Strip any content after tab character
            if isinstance(value, str) and '\t' in value:
                value = value.split('\t')[0]
            return value, 'chapter'
        
        return "1", "chapter"

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
            sections = self.citation_processor.process_text(
                text,
                default_author_id=file_author_id,
                default_work_id=file_work_id
            )
            
            # Organize sections into divisions
            divisions_dict = {}  # key: division_key, value: division_data
            current_tlg = None
            text_db_id = None
            
            # First pass - collect divisions and lines
            for section in sections:
                line_citation = section['citation']
                inherited_citation = section['inherited_citation']
                content = section['content']
                is_title = section['is_title']
                
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
                
                # Skip if we still can't determine the text
                if not text_db_id:
                    continue
                
                # Get division key and field based on citation information
                division_key, field_name = self._get_division_key_and_field(line_citation, inherited_citation)
                self.logger.debug(f"Got division key '{division_key}' for field '{field_name}'")
                
                # Create or get division
                if division_key not in divisions_dict:
                    # Initialize division data with all possible fields
                    division_data = {
                        "author_id_field": current_tlg.author_id if current_tlg else file_author_id,
                        "work_number_field": current_tlg.work_id if current_tlg else file_work_id,
                        "work_abbreviation_field": None,
                        "author_abbreviation_field": None,
                        "epistle": None,
                        "fragment": None,
                        "volume": None,
                        "book": None,
                        "chapter": None,
                        "section": None,
                        "page": None,
                        "line": None,
                        "lines": []
                    }
                    # Set the value in the correct field based on work structure
                    division_data[field_name] = division_key
                    divisions_dict[division_key] = division_data
                    self.stats['divisions_created'] += 1
                
                # Handle title lines
                if is_title:
                    # Update division title info and skip adding to lines
                    divisions_dict[division_key].update({
                        "is_title": True,
                        "title_number": line_citation.title_number if line_citation else None,
                        "title_text": content
                    })
                    # Skip adding title to lines since they're handled separately
                    continue
                
                # Get line number from citation hierarchy levels
                line_number = None
                if line_citation and line_citation.hierarchy_levels:
                    line_number = line_citation.hierarchy_levels.get('line')
                elif inherited_citation and inherited_citation.hierarchy_levels:
                    line_number = inherited_citation.hierarchy_levels.get('line')
                
                # Clean line number if present
                if line_number:
                    line_number = self._clean_line_number(line_number)
                
                # Add line to division with citation's line number or sequential number
                line_data = {
                    "line_number": line_number if line_number else str(len(divisions_dict[division_key]["lines"]) + 1),
                    "content": content
                }
                divisions_dict[division_key]["lines"].append(line_data)
                self.stats['processed_lines'] += 1
                
                # Track lines per division
                if division_key not in self.stats['lines_per_division']:
                    self.stats['lines_per_division'][division_key] = 0
                self.stats['lines_per_division'][division_key] += 1
            
            # Convert divisions dict to list, sorted by division key
            divisions = [div_data for _, div_data in sorted(
                divisions_dict.items(),
                key=lambda x: int(x[0]) if x[0].isdigit() else float('inf')
            )]
            
            # Create at least one division if none exist
            if not divisions and text_db_id:
                # Get author and work IDs
                author_id = current_tlg.author_id if current_tlg else file_author_id
                work_id = current_tlg.work_id if current_tlg else file_work_id
                
                # Get work structure
                structure = self.citation_parser.get_work_structure(author_id, work_id)
                if structure:
                    first_level = structure[0].lower()
                    self.logger.debug(f"Using {first_level} for initial division based on work structure: {structure}")
                    # Initialize all fields as None
                    division_data = {
                        "author_id_field": author_id,
                        "work_number_field": work_id,
                        "work_abbreviation_field": None,
                        "author_abbreviation_field": None,
                        "epistle": None,
                        "fragment": None,
                        "volume": None,
                        "book": None,
                        "chapter": None,
                        "section": None,
                        "page": None,
                        "lines": []
                    }
                    # Set value in correct field
                    division_data[first_level] = "1"
                    divisions = [division_data]
                else:
                    self.logger.debug("No work structure found, defaulting to chapter for initial division")
                    divisions = [{
                        "author_id_field": author_id,
                        "work_number_field": work_id,
                        "work_abbreviation_field": None,
                        "author_abbreviation_field": None,
                        "epistle": None,
                        "fragment": None,
                        "volume": None,
                        "book": None,
                        "chapter": "1",
                        "section": None,
                        "page": None,
                        "lines": []
                    }]
            
            # Second pass - create divisions and lines in database
            if divisions and text_db_id:
                # Create all divisions first
                division_objects = []
                for division in divisions:
                    # Normalize author_id_field
                    if division["author_id_field"]:
                        division["author_id_field"] = self._normalize_reference_code(division["author_id_field"])
                        
                    # Log division fields before creating object
                    self.logger.debug(f"Creating TextDivision with fields:")
                    for field in ["fragment", "volume", "chapter", "section", "page"]:
                        self.logger.debug(f"  {field} = {division.get(field)}")
                        
                    division_obj = TextDivision(
                        text_id=text_db_id,
                        author_id_field=division["author_id_field"],
                        work_number_field=division["work_number_field"],
                        work_abbreviation_field=division["work_abbreviation_field"],
                        author_abbreviation_field=division["author_abbreviation_field"],
                        epistle=division["epistle"],
                        fragment=division["fragment"],
                        volume=division["volume"],
                        book=division["book"],
                        chapter=division["chapter"],
                        section=division["section"],
                        page=division["page"],
                        is_title=division.get("is_title", False),
                        title_number=division.get("title_number"),
                        title_text=division.get("title_text")
                    )
                    self.session.add(division_obj)
                    division_objects.append((division_obj, division["lines"]))
                
                # Flush to get division IDs
                await self.session.flush()
                
                # Create lines for each division
                for division_obj, lines in division_objects:
                    # Sort lines by line number if available
                    sorted_lines = sorted(
                        lines,
                        key=lambda x: int(self._clean_line_number(x["line_number"])) 
                            if x["line_number"] and self._clean_line_number(x["line_number"]).isdigit() 
                            else float('inf')
                    )
                    
                    # Create lines
                    normalized_lines = []
                    for line in sorted_lines:
                        # Clean line number before storing
                        clean_line_number = self._clean_line_number(line["line_number"])
                        if not clean_line_number:
                            continue
                            
                        # Convert line number to integer
                        try:
                            line_number = int(clean_line_number)
                        except (ValueError, TypeError):
                            continue
                            
                        normalized_lines.append(
                            TextLine(
                                division_id=division_obj.id,
                                line_number=line_number,  # Now an integer
                                content=line["content"],
                                is_title=line.get("is_title", False)
                            )
                        )
                    
                    self.session.add_all(normalized_lines)
                
                # Flush all lines
                await self.session.flush()
                
                # Final commit
                await self.session.commit()
            
            self.stats['processed_files'] += 1
            
        except Exception as e:
            self.logger.error(f"Error processing file {file_path}: {str(e)}")
            await self.session.rollback()
            raise

    async def verify_migration(self) -> Dict:
        """Run post-migration verification with more lenient checks."""
        try:
            verification_results = await self.data_verifier.run_all_verifications()
            
            # Only raise error for critical issues
            critical_issues = []
            
            # Check relationship errors (missing required relationships)
            if verification_results.get("relationship_errors"):
                critical_issues.extend(verification_results["relationship_errors"])
            
            # Check content integrity (duplicate references, missing required fields)
            if verification_results.get("content_integrity_issues"):
                critical_issues.extend([
                    f"{issue['type']} for {issue['entity']} {issue.get('id', issue.get('reference_code'))}"
                    for issue in verification_results["content_integrity_issues"]
                ])
            
            # Line continuity issues are warnings only
            if verification_results.get("line_continuity_issues"):
                self.logger.warning(f"Found {len(verification_results['line_continuity_issues'])} line continuity issues")
            
            # Missing work structures are allowed
            if verification_results.get("incomplete_texts"):
                self.logger.info(f"Found {len(verification_results['incomplete_texts'])} texts with missing structures")
            
            # Only raise error for critical issues
            if critical_issues:
                raise MigrationError(f"Critical migration issues found: {', '.join(critical_issues)}")
                    
            return verification_results
        except Exception as e:
            self.logger.error(f"Error verifying migration: {str(e)}")
            raise

    async def migrate_directory(self, directory: Path, script_type: Optional[str] = None) -> None:
        """Migrate all text files in a directory."""
        try:
            # Get list of text files, excluding pipeline reports
            text_files = [
                f for f in directory.glob('**/*.txt')
                if 'pipeline_reports' not in str(f)
            ]
            
            # Process each file
            for file_path in tqdm(text_files, desc="Processing files", unit="file"):
                await self.process_text_file(file_path, script_type)
            
            # Run verification
            await self.verify_migration()
                
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

    from app.core.database import async_session_maker
    
    async with async_session_maker() as session:
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
