# Data Migration Guide

This guide provides instructions for executing and monitoring the migration of citation data to the new PostgreSQL database structure.

## Prerequisites

1. PostgreSQL 14+ installed and running
2. Database created and configured
3. Python environment with required dependencies:
   - SQLAlchemy 2.0+
   - asyncpg
   - tqdm
   - Python 3.9+

## Pre-Migration Steps

1. **Backup Existing Data**
   ```bash
   # Create a backup directory
   mkdir -p backups/$(date +%Y%m%d)
   
   # Copy all text files
   cp -r data/* backups/$(date +%Y%m%d)/
   ```

2. **Configure Database Connection**
   - Update `.env` file with database credentials:
   ```
   DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/amta_greek
   ```

3. **Verify Environment**
   ```bash
   # Check PostgreSQL connection
   python -c "from app.core.database import async_session; print('Database connection successful')"
   
   # Verify citation parser
   python -c "from toolkit.parsers.citation import CitationParser; print('Citation parser loaded')"
   ```
## Data Structure

### Text Divisions

A division is a logical unit of text organization that combines citation and structural components:

1. **Citation Components**:
   - Author ID field (e.g., [0086])
   - Work number field (e.g., [055])
   - Abbreviation/epithet field (optional, e.g., [Divis])
   - Fragment field (optional)

2. **Structural Components**:
   - Volume
   - Chapter
   - Section (e.g., 847a)
   - Lines within the division

3. **Title Components**:
   - Is title flag
   - Title number
   - Title text

Divisions are created:
- When a new chapter is encountered
- When title information is found
- When the TLG citation changes
- With a default chapter "1" if no chapter information exists

Example:
```
[TLG0627][055] Hippocrates Work
1.1 First chapter first line
1.2 First chapter second line
2.1 Second chapter first line
```
Creates:
- Division 1: Chapter 1 with lines 1 and 2
- Division 2: Chapter 2 with line 1

## Migration Options

### 1. Full Pipeline (Recommended)

The full pipeline handles text loading, NLP processing, and validation in one command. See [Pipeline Usage Guide](pipeline_usage.md) for detailed documentation.

```bash
# Basic usage
python -m toolkit.migration.process_full_pipeline --corpus-dir /path/to/texts

# Parallel processing for large datasets
python -m toolkit.migration.process_full_pipeline \
    --corpus-dir /path/to/texts \
    --parallel-loading \
    --max-workers 4 \
    --loading-batch-size 10 \
    --batch-size 20
```

Key features:
- Parallel text loading
- Parallel NLP processing
- Automatic validation
- Comprehensive error reporting
- Progress tracking
- Resource optimization

### 2. Manual Migration (Legacy)

For more granular control, you can run individual components:

1. **Test Migration**
   ```bash
   # Run migration tests
   pytest toolkit/tests/migration/test_citation_migrator.py -v
   ```

2. **Sample Data Migration**
   ```bash
   # Create a sample data directory
   mkdir -p data/sample
   
   # Copy a few files for testing
   cp data/some_text.txt data/sample/
   
   # Run migration on sample
   python -m toolkit.migration.citation_migrator --data-dir data/sample
   ```

3. **Full Migration**
   ```bash
   # Run the full migration
   python -m toolkit.migration.citation_migrator
   ```

## Monitoring Progress

1. **Pipeline Reports**
   - Location: `toolkit/migration/reports/`
   - Contains:
     - Execution time
     - Issues summary by category
     - Detailed error messages
     - Processing statistics
   - Automatically generated for each run
   - Named with timestamp for easy tracking
   - Preserved separately from source data
   - Easily accessible for review and troubleshooting

2. **Log Files**
   - Location: `toolkit/migration/logs/migration.log`
   - Contains detailed progress information
   - Rotates automatically (10MB per file, keeps 5 files)
   - Focused on real-time processing details

3. **Console Output**
   - Shows progress bars for each stage
   - Displays summary statistics
   - Reports any errors immediately

## Validation

1. **Automatic Validation**
   - Included in the full pipeline
   - Checks data completeness and integrity
   - Generates validation report

2. **Manual Database Checks**
   ```sql
   -- Check record counts
   SELECT COUNT(*) FROM authors;
   SELECT COUNT(*) FROM texts;
   SELECT COUNT(*) FROM text_divisions;
   SELECT COUNT(*) FROM text_lines;
   
   -- Check for orphaned records
   SELECT * FROM text_lines WHERE division_id NOT IN (SELECT id FROM text_divisions);
   SELECT * FROM text_divisions WHERE text_id NOT IN (SELECT id FROM texts);
   ```

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   - Verify PostgreSQL is running
   - Check connection string in .env
   - Ensure database user has proper permissions

2. **Performance Issues**
   - Adjust batch sizes and worker counts
   - Monitor system resources
   - See [Pipeline Usage Guide](pipeline_usage.md) for optimization tips

3. **Memory Issues**
   - Reduce batch sizes
   - Reduce number of workers
   - Monitor system memory usage

### Error Recovery

1. **If migration fails:**
   - Check pipeline reports in `toolkit/migration/reports/`
   - Review error details and stack traces
   - Fix any identified issues
   - Reset sequences if needed:
   ```bash
   python -m toolkit.migration.reset_sequences
   ```

2. **If validation fails:**
   ```sql
   -- Reset the database
   TRUNCATE TABLE text_lines CASCADE;
   TRUNCATE TABLE text_divisions CASCADE;
   TRUNCATE TABLE texts CASCADE;
   TRUNCATE TABLE authors CASCADE;
   ```

## Performance Optimization

1. **Database Indexes**
   ```sql
   -- Add indexes for common queries
   CREATE INDEX idx_text_lines_division ON text_lines(division_id);
   CREATE INDEX idx_text_divisions_text ON text_divisions(text_id);
   ```

2. **Parallel Processing**
   - Adjust workers based on CPU cores
   - Balance batch sizes for memory usage
   - See [Pipeline Usage Guide](pipeline_usage.md) for detailed settings

3. **Memory Usage**
   - Monitor with:
   ```bash
   watch -n 1 "ps aux | grep process_full_pipeline"
   ```

## Post-Migration Steps

1. **Verify Data**
   - Review pipeline reports in `toolkit/migration/reports/`
   - Check validation results
   - Verify sample records

2. **Clean Up**
   ```bash
   # Archive old reports (optional)
   tar -czf toolkit/migration/reports/archive_$(date +%Y%m%d).tar.gz toolkit/migration/reports/pipeline_report_*.txt
   
   # Remove temporary files
   rm -rf data/sample
   ```

3. **Documentation**
   - Review pipeline reports
   - Document any issues encountered
   - Update system documentation

## Support

For issues or questions:
1. Check the pipeline reports in `toolkit/migration/reports/`
2. Review the logs in `toolkit/migration/logs/`
3. Consult the [Pipeline Usage Guide](pipeline_usage.md)
4. Review the test suite for expected behavior
