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

    async def get_work(self, work_id: int) -> Optional[Text]:
        """Get a work by its ID.
        
        Args:
            work_id: The ID of the work to fetch
            
        Returns:
            Text object if found, None otherwise
        """
        stmt = select(Text).where(Text.id == work_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_division_content(self, division_id: int) -> Optional[str]:
        """Get the combined content of all lines in a division.
        
        Args:
            division_id: The ID of the division
            
        Returns:
            Combined content string if found, None otherwise
        """
        stmt = select(TextLine).where(
            TextLine.division_id == division_id
        ).order_by(TextLine.line_number)
        result = await self.session.execute(stmt)
        lines = result.scalars().all()
        
        if not lines:
            return None
            
        return "\n".join(line.content for line in lines)

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
                
                # Extract author and work IDs from filename
                filename = file_path.stem
                author_match = re.match(r'(?:TLG)?(\d+).*', filename)
                author_id = author_match.group(1) if author_match else "UNK000"
                work_id = self._extract_work_id(filename)
                
                text_data = {
                    "author_name": f"Author {author_id}",
                    "title": f"Work {work_id}" if work_id else "Pending",
                    "reference_code": work_id if work_id else "UNK000",
                    "author_id": author_id,  # Store author_id separately
                    "language_code": "grc",
                    "divisions": []
                }
                
                current_division = None
                
                # Process each line
                for line_obj in parsed_lines:
                    # Parse citation from line content
                    citation = line_obj.citation if hasattr(line_obj, 'citation') else None

                    if citation:
                        # Update text metadata when we find a citation with author/work info
                        if citation.work_id and text_data["title"] == "Pending":
                            text_data["title"] = f"Work {citation.work_id}"
                            text_data["reference_code"] = citation.work_id
                            
                        division = {
                            # Citation components with normalized author_id
                            "author_id_field": self._normalize_reference_code(citation.author_id) if citation.author_id else author_id,
                            "work_number_field": citation.work_id or work_id or "1",
                            "epithet_field": None,
                            "fragment_field": None,
                            # Structural components
                            "volume": citation.volume,
                            "chapter": citation.chapter,
                            "section": citation.section,
                            "lines": []
                        }
                        
                        if not current_division or citation.chapter != current_division.get("chapter"):
                            text_data["divisions"].append(division)
                            current_division = division

                    # Only add non-empty content lines
                    if line_obj.content.strip():
                        if not current_division:
                            # Create default division if none exists
                            current_division = {
                                "author_id_field": author_id,
                                "work_number_field": work_id or "1",
                                "epithet_field": None,
                                "fragment_field": None,
                                "volume": None,
                                "chapter": "1",  # Default chapter
                                "section": None,
                                "lines": []
                            }
                            text_data["divisions"].append(current_division)
                    
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
        author_id: Optional[str] = None,
        language_code: str = "grc",
        silent: bool = False
    ) -> Text:
        """Load a text and its divisions into the database."""
        try:
            # Use provided author_id or extract from author_name
            if not author_id and author_name.startswith("Author "):
                author_id = author_name.split("Author ")[-1]
            
            # Normalize author's reference code
            author_ref = self._normalize_reference_code(author_id) if author_id else "UNK000"
            
            # First try to get author by normalized reference_code
            author_stmt = select(Author).where(Author.reference_code == author_ref)
            author = (await self.session.execute(author_stmt)).scalar_one_or_none()
            
            if not author:
                # Create new author if none exists with this reference_code
                author = Author(
                    name=author_name,
                    reference_code=author_ref,
                    language_code=language_code
                )
                self.session.add(author)
                await self.session.flush()
                if not silent:
                    logger.info(f"Created new author: {author_name} ({author_ref})")
            elif author.name != author_name and author_name != "Pending":
                # Update author name if it has changed and isn't "Pending"
                author.name = author_name
                await self.session.flush()
                if not silent:
                    logger.info(f"Updated author name: {author_name} ({author_ref})")

            # Check if text already exists
            text_stmt = select(Text).where(
                Text.reference_code == reference_code,
                Text.author_id == author.id
            )
            text = (await self.session.execute(text_stmt)).scalar_one_or_none()
            
            if not text:
                # Create text if it doesn't exist
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
                # Normalize author_id_field in division
                if div.get("author_id_field"):
                    div["author_id_field"] = self._normalize_reference_code(div["author_id_field"])
                
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
                    author_id=text_data.get("author_id"),
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
