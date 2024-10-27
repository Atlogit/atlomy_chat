# Migration Tools Documentation

## Overview
The migration toolkit consists of several Python scripts designed to facilitate the transfer of text data from the existing file-based system to the new PostgreSQL database structure.

## Tools

### 1. CitationMigrator (citation_migrator.py)
The primary tool for migrating citation data to the PostgreSQL database.

#### Features
- Parses complex citation formats
- Handles hierarchical text structures
- Maintains relationships between authors, texts, divisions, and lines
- Implements caching for performance
- Provides detailed logging and error handling
- Integrates with validation components

#### Usage
```bash
# Process a single file
python citation_migrator.py --file path/to/file.txt

# Process an entire directory
python citation_migrator.py --dir path/to/directory

# Enable debug logging
python citation_migrator.py --file path/to/file.txt --debug
```

### 2. ContentValidator (content_validator.py)
Validates text content before migration to ensure data quality.

#### Features
- Basic content validation (empty, whitespace)
- Unicode content validation (Greek, Arabic, Chinese)
- Special characters validation
- Content length limits
- Invalid character detection

#### Usage
```python
from toolkit.migration.content_validator import ContentValidator, ContentValidationError

try:
    ContentValidator.validate(content)
except ContentValidationError as e:
    print(f"Content validation failed: {e}")
```

### 3. CitationProcessor (citation_processor.py)
Handles parsing and processing of citation formats.

#### Features
- Citation format parsing
- Line number extraction
- Section splitting
- Component validation

#### Usage
```python
from toolkit.migration.citation_processor import CitationProcessor

processor = CitationProcessor()
values = processor.extract_bracketed_values(citation)
content, is_title, line_number = processor.extract_line_info(line)
```

### 4. Text Viewing Utilities

#### Direct Database Access (view_texts_direct.py)
Provides direct database access using SQLAlchemy for viewing migrated texts.

Features:
- Uses SQLAlchemy's joinedload for efficient querying
- Displays full text hierarchy
- Shows author information and reference codes

Usage:
```python
python view_texts_direct.py
```

#### Service-Based Access (view_texts.py)
Uses the CorpusService abstraction layer for viewing texts.

Features:
- Implements service layer abstraction
- Provides structured data access
- Maintains separation of concerns

Usage:
```python
python view_texts.py
```

## Testing Structure

### Validation Tests
1. Content Validation (test_citation_content_validation.py)
   - Basic content validation
   - Unicode content validation
   - Special characters validation
   - Content length validation
   - Mixed content validation

2. Format Validation (test_citation_format_validation.py)
   - Citation format validation
   - Line number format validation
   - Mixed format validation
   - Sequential line numbers

3. Structural Validation (test_citation_structural_validation.py)
   - Hierarchical relationships
   - Division ordering
   - Line number continuity
   - Metadata consistency
   - Title line uniqueness

4. Basic Validation (test_citation_basic_validation.py)
   - Pre-migration validation
   - Post-migration verification
   - Error recovery and rollback

5. Integration Tests (test_citation_integration.py)
   - Database operations
   - Cross-component integration
   - End-to-end workflows

6. Performance Tests (test_citation_performance.py)
   - Large dataset handling
   - Batch processing
   - Memory usage
   - Query optimization

## Database Schema

### Core Tables
- authors: Stores author information
- texts: Contains text metadata and references
- text_divisions: Handles text structure and organization
- text_lines: Stores actual text content and metadata

### Key Relationships
- Author -> Text: One-to-many
- Text -> TextDivision: One-to-many
- TextDivision -> TextLine: One-to-many

## Best Practices

### Data Validation
1. Always validate content before processing
   - Check for invalid characters
   - Validate Unicode content
   - Verify content length
   - Ensure proper formatting

2. Validate citation structure
   - Check citation formats
   - Verify line numbers
   - Ensure hierarchical integrity

3. Post-migration verification
   - Verify data integrity
   - Check relationships
   - Validate content preservation

### Performance
1. Use caching for frequently accessed data
2. Implement batch processing for large datasets
3. Monitor memory usage
4. Use appropriate indexing
5. Consider async operations for I/O-bound tasks

### Error Handling
1. Implement comprehensive error logging
2. Use try-except blocks for specific errors
3. Maintain transaction integrity
4. Provide meaningful error messages
5. Include recovery procedures

## Future Improvements

### Planned Enhancements
1. Parallel processing support
2. Enhanced validation reporting
3. Progress tracking improvements
4. Performance optimizations
5. Additional verification tools

### Considerations
1. Scalability for larger datasets
2. Memory optimization
3. Error recovery procedures
4. Documentation updates
5. Testing coverage expansion
