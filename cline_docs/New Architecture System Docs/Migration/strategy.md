
# Migration Strategy Overview

## Phase 1: Database Setup

### 1. Initialize Database
```bash
# Create database
createdb amta_greek

# Initialize Alembic
alembic init migrations
```

### 2. Create Schema
```bash
# Generate initial migration
alembic revision --autogenerate -m "initial schema"

# Run migration
alembic upgrade head
```

## Phase 2: Data Migration

### 1. Prepare Source Data
- Export Coda tables to CSV
- Extract Elasticsearch data
- Prepare text files

### 2. Migration Order
1. Reference data (editions, authors)
2. Text structure (books, chapters)
3. Line content
4. NLP annotations
5. Lemmas and analyses

### 3. Validation Steps
- Check data integrity
- Verify parallel references
- Validate NLP data
- Test cross-references

## Migration Scripts

### Coda Migration
We don't currently have Coda data.
```python
async def migrate_coda_data(csv_file: str):
    async with AsyncSessionLocal() as session:
        data = read_coda_csv(csv_file)
        for row in data:
            # Create parallel entries
            modern = create_modern_entry(row)
            early = create_early_entry(row)
            
            # Link references
            link_parallel_entries(modern, early)
            
            session.add_all([modern, early])
        await session.commit()
```

### Elasticsearch Migration
```python
async def migrate_elastic_data():
    async with AsyncSessionLocal() as session:
        es_data = fetch_from_elasticsearch()
        for doc in es_data:
            lemma = create_lemma_entry(doc)
            references = create_references(doc)
            session.add_all([lemma, *references])
        await session.commit()
```

## Rollback Strategy

### 1. Backup
```bash
# Database backup
pg_dump ancient_texts_db > backup.sql

# Save migration state
alembic current > migration_state.txt
```

### 2. Rollback Procedure
```bash
# Revert migration
alembic downgrade -1

# Restore from backup if needed
psql ancient_texts_db < backup.sql
```

## Testing Strategy

### 1. Data Validation
```python
async def validate_migration():
    # Check record counts
    assert await count_texts() == expected_count
    
    # Verify parallel references
    assert await verify_parallel_entries()
    
    # Test cross-references
    assert await verify_cross_references()
```

### 2. Performance Testing
```python
async def test_performance():
    # Test common queries
    await measure_query_performance()
    
    # Test full-text search
    await measure_search_performance()
```

## Next Steps
```

