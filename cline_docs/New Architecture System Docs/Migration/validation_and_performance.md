# Migration Toolkit: Validation and Performance Documentation

## Overview
This document details the validation and performance features implemented in the migration toolkit, specifically focusing on content validation, data verification, and performance optimizations.

## Content Validation

### Pre-Migration Validation (ContentValidator)
The ContentValidator class provides comprehensive content validation:

1. Basic Content Validation
- Empty content check
- Whitespace-only content check
- Maximum content length validation

2. Script-Specific Validation
- Greek text validation
- Arabic text validation
- Chinese text validation
- Invalid character detection

3. Unicode and Special Characters
- Invalid Unicode range detection
- ASCII control character validation
- Script-specific character validation

Usage:
```python
from toolkit.migration.content_validator import ContentValidator

# Basic validation
ContentValidator.validate(content)

# Script-specific validation
ContentValidator.validate_script(content, "greek")
```

## Post-Migration Verification (DataVerifier)

### Relationship Verification
Verifies database relationships:
- Text -> Author relationships
- TextDivision -> Text relationships
- TextLine -> TextDivision relationships

### Content Integrity
Checks for:
- Duplicate reference codes
- Missing required fields
- Data consistency across tables

### Line Continuity
Ensures:
- Continuous line numbering within divisions
- Proper title line handling
- No gaps in line sequences

### Text Completeness
Verifies:
- All texts have required divisions
- All divisions have text lines
- Complete hierarchical structure

Usage:
```python
from toolkit.migration.content_validator import DataVerifier

verifier = DataVerifier(session)
results = await verifier.run_all_verifications()
```

## Performance Optimizations

### Batch Processing
The CitationMigrator implements efficient batch processing:

1. Text Line Batching
- Configurable batch size (default: 100)
- Automatic batch processing
- Memory-efficient operation

2. Database Operations
- Bulk inserts for text lines
- Efficient transaction management
- Automatic batch flushing

### Caching Mechanisms
Multiple caching layers:
1. Author Cache
- Maps author_id to database ID
- Reduces redundant queries
- Automatic cache population

2. Text Cache
- Maps (author_id, work_id) to text ID
- Optimizes text lookups
- Reduces database load

3. Division Line Counters
- Tracks line numbers per division
- Ensures proper sequencing
- Optimizes line number assignment

### Query Optimization
1. Efficient Queries
- Use of SQLAlchemy select statements
- Proper indexing utilization
- Minimized database roundtrips

2. Relationship Loading
- Strategic use of joins
- Efficient relationship traversal
- Optimized data retrieval

## Error Handling and Recovery

### Validation Errors
- Detailed error messages
- Error categorization
- Recovery suggestions

### Migration Errors
- Transaction management
- Rollback capabilities
- Error logging and reporting

### Verification Failures
- Comprehensive error reports
- Issue categorization
- Remediation guidance

## Usage Examples

### Basic Migration with Validation
```python
async with async_session() as session:
    migrator = CitationMigrator(session)
    
    # Process with script validation
    await migrator.process_text_file(file_path, script_type="greek")
    
    # Verify migration
    verification_results = await migrator.verify_migration()
```

### Batch Processing Configuration
```python
migrator = CitationMigrator(session)
migrator.batch_size = 200  # Adjust batch size
```

### Full Directory Migration
```python
await migrator.migrate_directory(directory_path, script_type="greek")
# Automatically includes:
# - Batch processing
# - Validation
# - Verification
# - Error handling
```

## Best Practices

1. Pre-Migration
- Validate content before migration
- Set appropriate batch sizes
- Configure logging

2. During Migration
- Monitor progress
- Check error logs
- Verify batch processing

3. Post-Migration
- Run full verification
- Check relationship integrity
- Validate data consistency

## Performance Considerations

1. Memory Usage
- Monitor batch size impact
- Watch cache growth
- Consider data volume

2. Database Load
- Balance batch sizes
- Monitor query performance
- Optimize indexes

3. Validation Overhead
- Configure appropriate validation levels
- Balance thoroughness vs. performance
- Consider script-specific needs

## Future Improvements

1. Planned Enhancements
- Parallel processing support
- Enhanced caching strategies
- Additional validation rules

2. Performance Optimization
- Query optimization
- Cache tuning
- Batch size optimization

3. Validation Extensions
- Additional script support
- Custom validation rules
- Performance profiling
