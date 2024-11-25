"""Content validation module for citation migration.

This module provides validation functionality for text content during migration.
Designed to preserve all data while capturing comprehensive migration insights.
"""
from typing import List, Dict, Optional, Set, Any
from sqlalchemy import select, func, and_, exists, or_  # Added or_ import
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
import logging
import traceback

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
        self.logger = logging.getLogger('migration.validation')
        self.detailed_errors = []

    async def verify_relationships(self) -> List[Dict[str, str]]:
        """
        Verify database relationships with comprehensive warning generation.
        
        Performs multiple levels of relationship validation:
        1. Orphaned entities
        2. Missing foreign key relationships
        3. Referential integrity checks
        """
        warnings = []

        try:
            # 1. Orphaned Entities Tracking
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

            # 2. Missing Foreign Key Relationships
            # Check for texts with non-existent author references
            invalid_text_authors = await self.session.execute(
                select(Text).filter(
                    Text.author_id.is_not(None) & 
                    ~exists().where(Author.id == Text.author_id)
                )
            )
            for text in invalid_text_authors.scalars():
                warnings.append({
                    "type": "invalid_author_reference",
                    "work_id": text.reference_code or str(text.id),
                    "message": f"Text {text.id} references non-existent author {text.author_id}"
                })

            # 3. Relationship Density Check
            # Warn if texts have unusually low or high number of divisions/lines
            text_division_counts = await self.session.execute(
                select(Text.id, func.count(TextDivision.id))
                .outerjoin(TextDivision, Text.id == TextDivision.text_id)
                .group_by(Text.id)
            )
            for text_id, division_count in text_division_counts:
                if division_count == 0:
                    warnings.append({
                        "type": "low_division_count",
                        "work_id": str(text_id),
                        "message": f"Text {text_id} has no divisions"
                    })
                elif division_count > 1000:  # Arbitrary high threshold
                    warnings.append({
                        "type": "high_division_count",
                        "work_id": str(text_id),
                        "message": f"Text {text_id} has unusually high number of divisions: {division_count}"
                    })

        except Exception as e:
            self.logger.error(f"Error during relationship verification: {str(e)}")
            self.logger.error(traceback.format_exc())
            warnings.append({
                "type": "verification_error",
                "work_id": "system",
                "message": f"Relationship verification failed: {str(e)}",
                "details": traceback.format_exc()
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
        Provides detailed insights into line number discrepancies.
        """
        warnings = []
        line_continuity_issues = []

        # Fetch all divisions with their lines, ordered by line number
        divisions = await self.session.execute(
            select(TextDivision).options(
                joinedload(TextDivision.text)  # Load associated text for context
            )
        )

        for division in divisions.scalars():
            # Fetch lines for this division, ordered by line number
            lines = await self.session.execute(
                select(TextLine)
                .filter(TextLine.division_id == division.id)
                .order_by(TextLine.line_number)
            )
            lines = list(lines.scalars())
            
            if lines:
                expected_number = 1
                discontinuities = []
                for line in lines:
                    if line.line_number != expected_number:
                        discontinuity = {
                            'expected': expected_number,
                            'actual': line.line_number,
                            'line_id': line.id,
                            'text_id': division.text_id,
                            'text_reference_code': division.text.reference_code if division.text else str(division.text_id),
                            'text_title': division.text.title if division.text else 'Unknown',
                            'division_id': division.id,
                            'division_reference_code': division.format_citation(abbreviated=True)
                        }
                        discontinuities.append(discontinuity)
                    
                    expected_number = line.line_number + 1
                
                if discontinuities:
                    warning = {
                        "type": "line_number_discontinuity",
                        "work_id": division.text.reference_code if division.text else str(division.id),
                        "message": f"Line number discontinuities in division {division.id}",
                        "details": discontinuities
                    }
                    warnings.append(warning)
                    
                    # Collect detailed line continuity issues
                    line_continuity_issues.append({
                        "text_id": division.text_id,
                        "text_reference_code": division.text.reference_code if division.text else str(division.text_id),
                        "text_title": division.text.title if division.text else 'Unknown',
                        "division_id": division.id,
                        "division_reference_code": division.format_citation(abbreviated=True),
                        "discontinuities": discontinuities
                    })

        # Log detailed line continuity issues
        if line_continuity_issues:
            self.logger.warning("Detailed Line Continuity Issues:")
            for issue in line_continuity_issues:
                self.logger.warning(
                    f"Text {issue['text_id']} (Ref: {issue['text_reference_code']}, Title: {issue['text_title']}): "
                    f"Line discontinuities in Division {issue['division_id']}"
                )
                for disc in issue['discontinuities']:
                    self.logger.warning(
                        f"  - Expected line {disc['expected']}, found line {disc['actual']} "
                        f"(Line ID: {disc['line_id']})"
                    )

        # Store detailed errors for comprehensive reporting
        if line_continuity_issues:
            self.detailed_errors.append({
                "type": "line_continuity",
                "category": "line_number_discontinuities",
                "count": len(line_continuity_issues),
                "details": line_continuity_issues
            })

        return warnings

    async def verify_text_completeness(self) -> List[Dict[str, str]]:
        """
        Text completeness verification with comprehensive warning generation.
        Provides detailed information about texts with missing lines.
        """
        warnings = []
        division_issues = []

        # Fetch all texts with their divisions, using joinedload for efficiency
        texts = await self.session.execute(
            select(Text).options(joinedload(Text.divisions))
        )

        for text in texts.scalars().unique():
            # Check if text has any divisions
            if not text.divisions:
                warnings.append({
                    "type": "text_without_divisions",
                    "work_id": text.reference_code or str(text.id),
                    "message": f"Text {text.id} contains no divisions"
                })
                continue

            # Track divisions without lines
            zero_line_divisions = []
            for division in text.divisions:
                # Skip title divisions from validation
                if division.is_title:
                    continue

                # Create a comprehensive division reference
                division_reference = f"{division.author_id_field}.{division.work_number_field}"
                if division.volume:
                    division_reference += f".{division.volume}"
                if division.chapter:
                    division_reference += f".{division.chapter}"

                # Check if division has any lines
                lines_count = await self.session.scalar(
                    select(func.count(TextLine.id)).filter(TextLine.division_id == division.id)
                )
                
                if lines_count == 0:
                    # Fetch additional context about the division
                    division_details = {
                        "division_id": division.id,
                        "division_reference_code": division_reference,
                        "text_id": text.id,
                        "text_reference_code": text.reference_code or str(text.id),
                        "text_title": text.title,
                        "division_details": {
                            "author_id": division.author_id_field,
                            "work_number": division.work_number_field,
                            "work_name": division.work_name,
                            "author_name": division.author_name,
                            "volume": division.volume,
                            "book": division.book,
                            "chapter": division.chapter,
                            "section": division.section,
                            "page": division.page,
                            "line": division.line,
                            "is_title": division.is_title,
                            "title_number": division.title_number,
                            "title_text": division.title_text
                        }
                    }

                    # Construct a comprehensive nearby lines query
                    nearby_lines_query = select(TextLine).join(
                        TextDivision, TextLine.division_id == TextDivision.id
                    ).filter(
                        (TextDivision.text_id == text.id) &
                        (TextLine.division_id != division.id) &
                        or_(
                            # Comprehensive structural matching
                            (division.volume is not None and TextDivision.volume == division.volume),
                            (division.book is not None and TextDivision.book == division.book),
                            (division.chapter is not None and TextDivision.chapter == division.chapter),
                            (division.section is not None and TextDivision.section == division.section),
                            (division.page is not None and TextDivision.page == division.page),
                            (division.line is not None and TextDivision.line == division.line)
                        )
                    ).order_by(TextLine.line_number).limit(20)
                    
                    nearby_lines = await self.session.execute(nearby_lines_query)
                    nearby_lines_details = []
                    for line in nearby_lines.scalars():
                        # Fetch division details for context
                        line_division = await self.session.scalar(
                            select(TextDivision).filter(TextDivision.id == line.division_id)
                        )
                        
                        nearby_lines_details.append({
                            "line_id": line.id,
                            "line_number": line.line_number,
                            "division_id": line.division_id,
                            "division_details": {
                                "volume": line_division.volume if line_division else None,
                                "book": line_division.book if line_division else None,
                                "chapter": line_division.chapter if line_division else None,
                                "section": line_division.section if line_division else None,
                                "page": line_division.page if line_division else None,
                                "line": line_division.line if line_division else None,
                            },
                            "content": line.content,
                            "categories": line.categories
                        })
                    
                    division_details["nearby_lines"] = nearby_lines_details

                    zero_line_divisions.append(division_details)

            # If divisions without lines exist, create a comprehensive warning
            if zero_line_divisions:
                warning = {
                    "type": "divisions_without_lines",
                    "work_id": text.reference_code or str(text.id),
                    "message": f"Text {text.id} has {len(zero_line_divisions)} divisions with no lines",
                    "details": zero_line_divisions
                }
                warnings.append(warning)
                
                # Collect detailed division issues
                division_issues.append({
                    "text_id": text.id,
                    "text_reference_code": text.reference_code or str(text.id),
                    "text_title": text.title,
                    "divisions_without_lines": zero_line_divisions
                })

        # Log detailed division issues
        if division_issues:
            self.logger.warning("Detailed Divisions Without Lines:")
            for issue in division_issues:
                self.logger.warning(
                    f"Text {issue['text_id']} (Ref: {issue['text_reference_code']}, Title: {issue['text_title']}): "
                    f"{len(issue['divisions_without_lines'])} divisions without lines"
                )
                for div in issue['divisions_without_lines']:
                    self.logger.warning(
                        f"  - Division {div['division_id']} (Ref: {div.get('division_reference_code', 'N/A')})"
                    )
                    # Log additional division details
                    for key, value in div['division_details'].items():
                        if value is not None:
                            self.logger.warning(f"    {key}: {value}")
                    
                    # Log nearby lines if available
                    if div.get('nearby_lines'):
                        self.logger.warning("    Nearby Lines:")
                        for line in div['nearby_lines']:
                            self.logger.warning(
                                f"      Line {line['line_id']} (Div: {line['division_id']}, Number: {line['line_number']}):"
                                f" {line['content'][:100]}..."
                            )
                            # Log division details for nearby lines
                            if line.get('division_details'):
                                self.logger.warning("        Division Context:")
                                for key, value in line['division_details'].items():
                                    if value is not None:
                                        self.logger.warning(f"          {key}: {value}")

        # Store detailed errors for comprehensive reporting
        if division_issues:
            self.detailed_errors.append({
                "type": "text_completeness",
                "category": "divisions_without_lines",
                "count": len(division_issues),
                "details": division_issues
            })

        return warnings

    async def run_all_verifications(self) -> Dict[str, List[Dict[str, str]]]:
            """
            Run all verification checks with comprehensive warning generation.
            """
            try:
                verification_results = {
                    "relationship_warnings": await self.verify_relationships(),
                    "content_integrity_warnings": await self.verify_content_integrity(),
                    "line_continuity_warnings": await self.verify_line_continuity(),
                    "text_completeness_warnings": await self.verify_text_completeness()
                }

                # Collect all warnings
                all_warnings = []
                for category, warnings in verification_results.items():
                    all_warnings.extend(warnings)

                # Log warnings if any exist
                if all_warnings:
                    self.logger.warning(f"Validation found {len(all_warnings)} warnings")
                    for warning in all_warnings:
                        self.logger.warning(f"{warning['type']}: {warning['message']}")

                return verification_results

            except Exception as e:
                self.logger.error(f"Comprehensive verification failed: {str(e)}")
                self.logger.error(traceback.format_exc())
                return {
                    "verification_error": [{
                        "type": "system_error",
                        "work_id": "system",
                        "message": f"Comprehensive verification failed: {str(e)}",
                        "details": traceback.format_exc()
                    }]
                }