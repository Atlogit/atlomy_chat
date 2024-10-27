"""
Database loader for storing processed texts in PostgreSQL.

This module handles the storage of NLP-processed texts in the database,
maintaining relationships between authors, texts, divisions, and lines.
"""

import logging
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert
from tqdm import tqdm

from app.models.author import Author
from app.models.text import Text
from app.models.text_division import TextDivision
from app.models.text_line import TextLine
from toolkit.parsers.text import TextParser
from toolkit.parsers.citation import CitationParser

logger = logging.getLogger(__name__)

class DatabaseLoader:
    """Handles loading processed texts into PostgreSQL database."""
    
    def __init__(self, session: AsyncSession):
        """Initialize the database loader."""
        self.session = session
        self.text_parser = TextParser()
        self.citation_parser = CitationParser()

    async def load_corpus_directory(self, 
                                 corpus_dir: Path,
                                 file_pattern: str = "TLG*") -> List[Text]:
        """Load all texts from a directory sequentially."""
        corpus_dir = Path(corpus_dir)
        if not corpus_dir.exists():
            raise ValueError(f"Directory does not exist: {corpus_dir}")

        text_files = list(corpus_dir.glob(file_pattern))
        logger.info(f"Found {len(text_files)} text files in {corpus_dir}")

        texts_data = []
        for file_path in text_files:
            try:
                # Parse text file
                parsed_lines = await self.text_parser.parse_file(file_path)
                
                # Extract text metadata from filename
                text_id = file_path.stem  # e.g., "TLG0627_hippocrates-050"
                
                # Extract TLG code for reference_code
                match = re.match(r'(TLG\d+).*', text_id)
                reference_code = match.group(1) if match else "UNK000"
                
                text_data = {
                    "author_name": "Unknown",
                    "title": text_id,
                    "reference_code": reference_code,
                    "language_code": "grc",
                    "divisions": []
                }
                
                current_division = None
                
                # Process each line
                for line_obj in parsed_lines:
                    # Parse citation from line content
                    remaining, citations = self.citation_parser.parse_citation(line_obj.content)
                    
                    if citations:
                        citation = citations[0]  # Use first citation if multiple found
                        division = {
                            # Citation components
                            "author_id_field": citation.author_id or "1",
                            "work_number_field": citation.work_id or "1",
                            "epithet_field": None,
                            "fragment_field": None,
                            # Structural components
                            "volume": citation.volume,
                            "chapter": citation.chapter,
                            "section": citation.division or citation.line or "1",
                            "lines": []
                        }
                        text_data["divisions"].append(division)
                        current_division = division
                        continue  # Skip adding citation line as content
                    
                    if not current_division:
                        current_division = {
                            "author_id_field": "1",
                            "work_number_field": "1",
                            "epithet_field": None,
                            "fragment_field": None,
                            "volume": None,
                            "chapter": None,
                            "section": "1",
                            "lines": []
                        }
                        text_data["divisions"].append(current_division)
                    
                    # Only add non-citation lines as content
                    if line_obj.content.strip():
                        line_data = {
                            "line_number": len(current_division["lines"]) + 1,
                            "content": line_obj.content
                        }
                        current_division["lines"].append(line_data)
                
                texts_data.append(text_data)
                logger.info(f"Processed file: {file_path}")
                
            except Exception as e:
                logger.error(f"Error processing file {file_path}: {e}")
                continue

        return await self.bulk_load_texts(texts_data)

    async def load_text(
        self,
        author_name: str,
        text_title: str,
        reference_code: str,
        divisions: List[Dict[str, Any]],
        language_code: str = "grc",
        silent: bool = False
    ) -> Text:
        """Load a text and its divisions into the database."""
        try:
            # Get or create author
            author_stmt = select(Author).where(Author.name == author_name)
            author = (await self.session.execute(author_stmt)).scalar_one_or_none()
            
            if not author:
                author = Author(
                    name=author_name,
                    reference_code=reference_code,
                    language_code=language_code
                )
                self.session.add(author)
                await self.session.flush()
                if not silent:
                    logger.info(f"Created new author: {author_name}")

            # Create text
            text = Text(
                author_id=author.id,
                title=text_title,
                reference_code=reference_code
            )
            self.session.add(text)
            await self.session.flush()

            # Create divisions and lines
            total_lines = sum(len(div.get("lines", [])) for div in divisions)
            if not silent:
                logger.info(f"Loading text: {text_title} ({total_lines} lines)")

            for div in divisions:
                division = TextDivision(
                    text_id=text.id,
                    author_id_field=div["author_id_field"],
                    work_number_field=div["work_number_field"],
                    epithet_field=div.get("epithet_field"),
                    fragment_field=div.get("fragment_field"),
                    volume=div.get("volume"),
                    chapter=div.get("chapter"),
                    section=div.get("section")
                )
                self.session.add(division)
                await self.session.flush()

                # Add lines for this division
                lines = [
                    TextLine(
                        division_id=division.id,
                        line_number=line_data.get("line_number"),
                        content=line_data["content"]
                    )
                    for line_data in div.get("lines", [])
                ]
                self.session.add_all(lines)

            await self.session.commit()
            if not silent:
                logger.info(f"✓ Successfully loaded {text_title}")
            return text

        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error loading text {text_title}: {e}")
            raise

    async def bulk_load_texts(
        self,
        texts_data: List[Dict[str, Any]]
    ) -> List[Text]:
        """Load multiple texts in bulk."""
        created_texts = []
        total_texts = len(texts_data)
        logger.info(f"Starting bulk load of {total_texts} texts")
        
        try:
            for i, text_data in enumerate(texts_data, 1):
                text = await self.load_text(
                    author_name=text_data["author_name"],
                    text_title=text_data["title"],
                    reference_code=text_data["reference_code"],
                    divisions=text_data["divisions"],
                    language_code=text_data.get("language_code", "grc"),
                    silent=True
                )
                created_texts.append(text)
                logger.info(f"[{i}/{total_texts}] Loaded: {text_data['title']}")
            
            logger.info(f"✓ Successfully loaded all {total_texts} texts")
            return created_texts

        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error in bulk loading texts: {e}")
            raise
