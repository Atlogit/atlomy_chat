"""Content validation module for citation migration.

This module provides validation functionality for text content during migration.
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
    """Validates text content for migration."""

    # Maximum allowed content length
    MAX_CONTENT_LENGTH = 10000
    
    # Invalid Unicode ranges
    INVALID_UNICODE = [
        (0xFFFE, 0xFFFF),
        (0x1FFFE, 0x1FFFF)
    ]
    
    # Invalid ASCII control characters (excluding tab 0x9 and newline 0xA)
    INVALID_ASCII = set(range(0x00, 0x09)) | set(range(0x0B, 0x20)) | {0x7F} | set(range(0x80, 0xA0))

    # Valid script ranges
    GREEK_RANGE = [(0x0370, 0x03FF), (0x1F00, 0x1FFF)]  # Greek and Coptic, Greek Extended
    ARABIC_RANGE = [(0x0600, 0x06FF), (0x0750, 0x077F)]  # Arabic, Arabic Supplement
    CHINESE_RANGE = [(0x4E00, 0x9FFF)]  # CJK Unified Ideographs

    @classmethod
    def validate(cls, content: str) -> None:
        """Validate text content before migration."""
        if not content or content.isspace():
            raise ContentValidationError("Content cannot be empty or whitespace only")
            
        if len(content) > cls.MAX_CONTENT_LENGTH:
            raise ContentValidationError(f"Content length exceeds maximum of {cls.MAX_CONTENT_LENGTH} characters")
            
        # Check for invalid ASCII control characters
        for char in content:
            if ord(char) in cls.INVALID_ASCII:
                raise ContentValidationError(f"Invalid ASCII control character: {hex(ord(char))}")
                
        # Check for invalid Unicode ranges
        for char in content:
            code_point = ord(char)
            for start, end in cls.INVALID_UNICODE:
                if start <= code_point <= end:
                    raise ContentValidationError(f"Invalid Unicode character: {hex(code_point)}")
                    
        return True

    @classmethod
    def validate_script(cls, content: str, script_type: str) -> bool:
        """Validate content matches expected script type."""
        if script_type not in ["greek", "arabic", "chinese"]:
            raise ValueError("Unsupported script type")

        script_ranges = {
            "greek": cls.GREEK_RANGE,
            "arabic": cls.ARABIC_RANGE,
            "chinese": cls.CHINESE_RANGE
        }

        ranges = script_ranges[script_type]
        for char in content:
            code_point = ord(char)
            if not any(start <= code_point <= end for start, end in ranges):
                if not char.isspace() and not char.isascii():
                    raise ContentValidationError(
                        f"Character '{char}' ({hex(code_point)}) is not valid {script_type} script"
                    )
        return True

class DataVerifier:
    """Handles post-migration verification and data integrity checks."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def verify_relationships(self) -> List[str]:
        """Verify all database relationships are intact."""
        errors = []

        # Check Text -> Author relationships
        orphaned_texts = await self.session.execute(
            select(Text).filter(Text.author_id.is_(None))
        )
        if orphaned_texts.scalars().first():
            errors.append("Found texts without authors")

        # Check TextDivision -> Text relationships
        orphaned_divisions = await self.session.execute(
            select(TextDivision).filter(TextDivision.text_id.is_(None))
        )
        if orphaned_divisions.scalars().first():
            errors.append("Found text divisions without texts")

        # Check TextLine -> TextDivision relationships
        orphaned_lines = await self.session.execute(
            select(TextLine).filter(TextLine.division_id.is_(None))
        )
        if orphaned_lines.scalars().first():
            errors.append("Found text lines without divisions")

        return errors

    async def verify_content_integrity(self) -> List[Dict]:
        """Verify content integrity across all texts."""
        issues = []

        # Check for duplicate reference codes
        duplicate_authors = await self.session.execute(
            select(Author.reference_code, func.count(Author.id))
            .group_by(Author.reference_code)
            .having(func.count(Author.id) > 1)
        )
        for ref_code, count in duplicate_authors.all():
            issues.append({
                "type": "duplicate_reference",
                "entity": "author",
                "reference_code": ref_code,
                "count": count
            })

        # Check for missing required fields
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
            issues.append({
                "type": "missing_required_field",
                "entity": "text",
                "id": text.id,
                "missing_fields": [
                    field for field in ["reference_code", "title"]
                    if not getattr(text, field)
                ]
            })

        return issues

    async def verify_line_continuity(self) -> List[Dict]:
        """Verify text line numbers are continuous within divisions."""
        discontinuities = []

        # Get all divisions
        divisions = await self.session.execute(
            select(TextDivision)
        )

        for division in divisions.scalars():
            lines = await self.session.execute(
                select(TextLine)
                .filter(TextLine.division_id == division.id)
                .order_by(TextLine.line_number)
            )
            lines = lines.scalars().all()
            
            # Check for gaps in line numbers
            if lines:
                expected_number = 1
                for line in lines:
                    if line.line_number != expected_number:
                        discontinuities.append({
                            "division_id": division.id,
                            "expected": expected_number,
                            "found": line.line_number
                        })
                    expected_number += 1

        return discontinuities

    async def verify_text_completeness(self) -> List[Dict]:
        """Verify all texts have expected components."""
        incomplete_texts = []

        texts = await self.session.execute(select(Text))
        for text in texts.scalars():
            divisions = await self.session.execute(
                select(TextDivision).filter(TextDivision.text_id == text.id)
            )
            divisions = divisions.scalars().all()

            if not divisions:
                incomplete_texts.append({
                    "text_id": text.id,
                    "issue": "no_divisions"
                })
                continue

            for division in divisions:
                lines = await self.session.execute(
                    select(TextLine).filter(TextLine.division_id == division.id)
                )
                if not lines.scalars().first():
                    incomplete_texts.append({
                        "text_id": text.id,
                        "division_id": division.id,
                        "issue": "no_lines"
                    })

        return incomplete_texts

    async def run_all_verifications(self) -> Dict:
        """Run all verification checks and return combined results."""
        return {
            "relationship_errors": await self.verify_relationships(),
            "content_integrity_issues": await self.verify_content_integrity(),
            "line_continuity_issues": await self.verify_line_continuity(),
            "incomplete_texts": await self.verify_text_completeness()
        }
