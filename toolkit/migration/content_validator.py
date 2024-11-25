"""Content validation module for citation migration.

This module provides validation functionality for text content during migration.
Designed to preserve all data while capturing comprehensive migration insights.
"""
from typing import List, Dict, Optional, Set
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.author import Author
from app.models.text import Text
from app.models.text_division import TextDivision
from app.models.text_line import TextLine

class ContentValidationError(Exception):
    """Exception raised for content validation errors."""
    pass

class ContentValidator:
    """Validates text content for migration with maximum data preservation and warning generation."""

    # Extremely high content length limit
    MAX_CONTENT_LENGTH = 500000
    
    # Minimal invalid Unicode ranges
    INVALID_UNICODE = []
    
    # Minimal invalid ASCII control characters
    INVALID_ASCII = set()

    # Expanded script ranges
    GREEK_RANGE = [(0x0370, 0x03FF), (0x1F00, 0x1FFF)]  # Greek and Coptic, Greek Extended
    ARABIC_RANGE = [(0x0600, 0x06FF), (0x0750, 0x077F)]  # Arabic, Arabic Supplement
    CHINESE_RANGE = [(0x4E00, 0x9FFF)]  # CJK Unified Ideographs
    LATIN_RANGE = [(0x0000, 0x007F), (0x0080, 0x00FF)]  # Basic Latin and Latin-1 Supplement
    CYRILLIC_RANGE = [(0x0400, 0x04FF)]  # Cyrillic

    @classmethod
    def validate(cls, content: str, work_id: Optional[str] = None) -> List[Dict[str, str]]:
        """
        Validate text content with maximum leniency.
        Generates comprehensive warnings while preserving all content.
        """
        warnings = []

        # Detailed content analysis
        if not content:
            warnings.append({
                "type": "empty_content",
                "work_id": work_id,
                "message": "Empty content detected"
            })
            return warnings

        # Extremely lenient content length check with detailed warning
        if len(content) > cls.MAX_CONTENT_LENGTH:
            warnings.append({
                "type": "content_length",
                "work_id": work_id,
                "message": f"Content length exceeds {cls.MAX_CONTENT_LENGTH} characters. Full content will be preserved."
            })

        # Character diversity analysis
        char_types = set()
        for char in content:
            code_point = ord(char)
            if char.isalpha():
                char_types.add('alphabetic')
            if char.isdigit():
                char_types.add('numeric')
            if char.isspace():
                char_types.add('whitespace')
            if not char.isascii():
                char_types.add('non_ascii')

        if len(char_types) < 2:
            warnings.append({
                "type": "limited_character_diversity",
                "work_id": work_id,
                "message": f"Limited character diversity detected: {', '.join(char_types)}"
            })
                
        return warnings

    @classmethod
    def validate_script(cls, content: str, script_type: str, work_id: Optional[str] = None) -> List[Dict[str, str]]:
        """
        Validate content script with maximum inclusivity and detailed warning generation.
        """
        warnings = []

        # Expanded script support
        supported_scripts = ["greek", "arabic", "chinese", "english", "latin", "cyrillic", "mixed"]
        if script_type not in supported_scripts:
            warnings.append({
                "type": "script_validation",
                "work_id": work_id,
                "message": f"Expanded script support requested: {script_type}"
            })

        # Comprehensive script range analysis
        script_ranges = {
            "greek": cls.GREEK_RANGE,
            "arabic": cls.ARABIC_RANGE,
            "chinese": cls.CHINESE_RANGE,
            "latin": cls.LATIN_RANGE,
            "cyrillic": cls.CYRILLIC_RANGE
        }

        # Detailed script character tracking
        script_char_counts = {script: 0 for script in script_ranges.keys()}
        total_chars = 0

        for char in content:
            total_chars += 1
            code_point = ord(char)
            
            # Track character distribution across script ranges
            for script, ranges in script_ranges.items():
                if any(start <= code_point <= end for start, end in ranges):
                    script_char_counts[script] += 1

        # Generate warnings about script character distribution
        if total_chars > 0:
            mixed_script_warning = []
            for script, count in script_char_counts.items():
                percentage = (count / total_chars) * 100
                if 0 < percentage < 10:
                    mixed_script_warning.append(f"{script}: {percentage:.2f}%")

            if mixed_script_warning:
                warnings.append({
                    "type": "mixed_script_distribution",
                    "work_id": work_id,
                    "message": f"Potential mixed script content: {', '.join(mixed_script_warning)}"
                })
        
        return warnings

class DataVerifier:
    """Handles post-migration verification with comprehensive warning generation."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def verify_relationships(self) -> List[Dict[str, str]]:
        """
        Verify database relationships with comprehensive warning generation.
        """
        warnings = []

        # Detailed orphaned entity tracking
        orphaned_texts = await self.session.execute(
            select(Text).filter(Text.author_id.is_(None))
        )
        for text in orphaned_texts.scalars():
            warnings.append({
                "type": "orphaned_text",
                "work_id": text.reference_code or str(text.id),
                "message": f"Text {text.id} lacks author association"
            })

        orphaned_divisions = await self.session.execute(
            select(TextDivision).filter(TextDivision.text_id.is_(None))
        )
        for division in orphaned_divisions.scalars():
            warnings.append({
                "type": "orphaned_division",
                "work_id": division.reference_code or str(division.id),
                "message": f"Division {division.id} lacks text association"
            })

        orphaned_lines = await self.session.execute(
            select(TextLine).filter(TextLine.division_id.is_(None))
        )
        for line in orphaned_lines.scalars():
            warnings.append({
                "type": "orphaned_line",
                "work_id": line.reference_code or str(line.id),
                "message": f"Line {line.id} lacks division association"
            })

        return warnings

    async def verify_content_integrity(self) -> List[Dict[str, str]]:
        """
        Verify content integrity with comprehensive warning generation.
        """
        warnings = []

        # Detailed reference code analysis
        duplicate_authors = await self.session.execute(
            select(Author.reference_code, func.count(Author.id))
            .group_by(Author.reference_code)
            .having(func.count(Author.id) > 1)
        )
        for ref_code, count in duplicate_authors.all():
            warnings.append({
                "type": "duplicate_reference",
                "work_id": ref_code,
                "message": f"Multiple authors share reference code: {count} occurrences"
            })

        # Texts with missing critical fields
        texts_missing_fields = await self.session.execute(
            select(Text)
            .filter(
                (Text.reference_code.is_(None)) |
                (Text.reference_code == "") |
                (Text.title.is_(None)) |
                (Text.title == "")
            )
        )
        for text in texts_missing_fields.scalars():
            missing_fields = [
                field for field in ["reference_code", "title"]
                if not getattr(text, field)
            ]
            warnings.append({
                "type": "incomplete_text_metadata",
                "work_id": text.reference_code or str(text.id),
                "message": f"Text {text.id} missing fields: {', '.join(missing_fields)}"
            })

        return warnings

    async def verify_line_continuity(self) -> List[Dict[str, str]]:
        """
        Line continuity verification with comprehensive warning generation.
        """
        warnings = []

        # Detailed line number discontinuity tracking
        divisions = await self.session.execute(select(TextDivision))

        for division in divisions.scalars():
            lines = await self.session.execute(
                select(TextLine)
                .filter(TextLine.division_id == division.id)
                .order_by(TextLine.line_number)
            )
            lines = lines.scalars().all()
            
            if lines:
                expected_number = 1
                discontinuities = []
                for line in lines:
                    if line.line_number != expected_number:
                        discontinuities.append({
                            'expected': expected_number,
                            'actual': line.line_number
                        })
                    expected_number += 1
                
                if discontinuities:
                    warnings.append({
                        "type": "line_number_discontinuity",
                        "work_id": division.reference_code or str(division.id),
                        "message": f"Line number discontinuities in division {division.id}",
                        "details": discontinuities
                    })

        return warnings

    async def verify_text_completeness(self) -> List[Dict[str, str]]:
        """
        Text completeness verification with comprehensive warning generation.
        """
        warnings = []

        texts = await self.session.execute(select(Text))
        for text in texts.scalars():
            divisions = await self.session.execute(
                select(TextDivision).filter(TextDivision.text_id == text.id)
            )
            divisions = divisions.scalars().all()

            if not divisions:
                warnings.append({
                    "type": "text_without_divisions",
                    "work_id": text.reference_code or str(text.id),
                    "message": f"Text {text.id} contains no divisions"
                })
                continue

            zero_line_divisions = []
            for division in divisions:
                lines = await self.session.execute(
                    select(TextLine).filter(TextLine.division_id == division.id)
                )
                if not lines.scalars().first():
                    zero_line_divisions.append(division.id)

            if zero_line_divisions:
                warnings.append({
                    "type": "divisions_without_lines",
                    "work_id": text.reference_code or str(text.id),
                    "message": f"Text {text.id} has divisions with no lines",
                    "details": zero_line_divisions
                })

        return warnings

    async def run_all_verifications(self) -> Dict[str, List[Dict[str, str]]]:
        """
        Run all verification checks with comprehensive warning generation.
        """
        return {
            "relationship_warnings": await self.verify_relationships(),
            "content_integrity_warnings": await self.verify_content_integrity(),
            "line_continuity_warnings": await self.verify_line_continuity(),
            "text_completeness_warnings": await self.verify_text_completeness()
        }
