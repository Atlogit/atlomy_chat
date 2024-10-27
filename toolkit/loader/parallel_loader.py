"""
Parallel database loader for efficient text loading.

This module provides parallel loading capabilities while maintaining
database consistency and proper relationship handling.
"""

import asyncio
import logging
import os
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from tqdm import tqdm

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.author import Author
from app.models.text import Text
from app.models.text_division import TextDivision
from app.models.text_line import TextLine
from toolkit.parsers.citation import CitationParser
from toolkit.parsers.text import TextParser

logger = logging.getLogger(__name__)

@dataclass
class TextBatch:
    """Represents a batch of texts to be loaded."""
    batch_id: int
    texts: List[Dict[str, Any]]

class ParallelDatabaseLoader:
    """Handles parallel loading of texts into the database."""

    def __init__(self, 
                 session: AsyncSession,
                 max_workers: int = 4,
                 batch_size: int = 5):
        """Initialize the parallel loader."""
        self.session = session
        self.max_workers = max_workers
        self.batch_size = batch_size
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.authors_cache = {}
        self.text_parser = TextParser()
        self.citation_parser = CitationParser()

    async def _get_or_create_author(self, 
                                  author_name: str, 
                                  reference_code: Optional[str] = None,
                                  language_code: str = "grc") -> Author:
        """Get existing author or create new one."""
        if author_name in self.authors_cache:
            return self.authors_cache[author_name]

        # Use provided reference code or generate one
        if not reference_code:
            reference_code = "UNK000" if author_name == "Unknown" else f"AUT{hash(author_name) % 1000:03d}"

        stmt = select(Author).where(Author.reference_code == reference_code)
        result = await self.session.execute(stmt)
        author = result.scalar_one_or_none()

        if not author:
            author = Author(
                name=author_name,
                reference_code=reference_code,
                language_code=language_code
            )
            self.session.add(author)
            await self.session.flush()

        self.authors_cache[author_name] = author
        return author

    async def _process_text_file(self, file_path: Path) -> Dict[str, Any]:
        """Process a single text file and return structured data."""
        try:
            # Parse text file using TextParser
            parsed_lines = await self.text_parser.parse_file(file_path)
            
            # Extract text metadata from filename
            text_id = file_path.stem  # e.g., "TLG0627_hippocrates-050"
            
            # Extract TLG code for reference_code
            match = re.match(r'(TLG\d+).*', text_id)
            reference_code = match.group(1) if match else "UNK000"
            
            # Structure the data for database loading
            text_data = {
                "author_name": "Unknown",
                "title": text_id,
                "reference_code": reference_code,
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
                        "line": citation.division or citation.line or "1",
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
            
            return text_data
            
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
            raise

    async def _process_text_batch(self, batch: TextBatch) -> List[Text]:
        """Process a batch of texts concurrently."""
        created_texts = []
        
        try:
            for text_data in batch.texts:
                author = await self._get_or_create_author(
                    text_data["author_name"],
                    reference_code=text_data.get("reference_code")
                )

                text = Text(
                    author_id=author.id,
                    title=text_data["title"],
                    reference_code=text_data["reference_code"]
                )
                self.session.add(text)
                await self.session.flush()

                for div in text_data["divisions"]:
                    division = TextDivision(
                        text_id=text.id,
                        author_id_field=div["author_id_field"],
                        work_number_field=div["work_number_field"],
                        epithet_field=div.get("epithet_field"),
                        fragment_field=div.get("fragment_field"),
                        volume=div.get("volume"),
                        chapter=div.get("chapter"),
                        line=div.get("line")
                    )
                    self.session.add(division)
                    await self.session.flush()

                    lines = [
                        TextLine(
                            division_id=division.id,
                            line_number=line_data.get("line_number"),
                            content=line_data["content"]
                        )
                        for line_data in div.get("lines", [])
                    ]
                    self.session.add_all(lines)

                created_texts.append(text)

            await self.session.commit()
            return created_texts

        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error processing batch {batch.batch_id}: {e}")
            raise

    async def load_texts_parallel(self, texts_data: List[Dict[str, Any]]) -> List[Text]:
        """Load multiple texts in parallel batches."""
        total_texts = len(texts_data)
        batches = []
        for i in range(0, total_texts, self.batch_size):
            batch_texts = texts_data[i:i + self.batch_size]
            batches.append(TextBatch(batch_id=len(batches), texts=batch_texts))

        all_texts = []
        with tqdm(total=total_texts, desc="Loading texts", unit="text") as pbar:
            for batch in batches:
                try:
                    texts = await self._process_text_batch(batch)
                    all_texts.extend(texts)
                    pbar.update(len(batch.texts))
                except Exception as e:
                    logger.error(f"Failed to process batch {batch.batch_id}: {e}")
                    raise

        return all_texts

    async def load_corpus_directory_parallel(self, 
                                          corpus_dir: Path,
                                          file_pattern: str = "TLG*") -> List[Text]:
        """Load all texts from a directory in parallel."""
        corpus_dir = Path(corpus_dir)
        if not corpus_dir.exists():
            raise ValueError(f"Directory does not exist: {corpus_dir}")

        text_files = list(corpus_dir.glob(file_pattern))
        texts_data = []
        with tqdm(total=len(text_files), desc="Processing files", unit="file") as pbar:
            for file_path in text_files:
                try:
                    text_data = await self._process_text_file(file_path)
                    texts_data.append(text_data)
                    pbar.update(1)
                except Exception as e:
                    logger.error(f"Error processing {file_path}: {e}")
                    continue

        return await self.load_texts_parallel(texts_data)
