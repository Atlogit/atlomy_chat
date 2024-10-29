# Codebase Summary

## Core Components

### 1. Database Layer
- PostgreSQL with SQLAlchemy ORM
- Alembic migrations for schema changes
- Enhanced text_divisions with author/work names
- Added sentence-based citation support
- Implemented direct citation linking

### 2. Services Layer

#### LexicalService
- Manages lexical value creation and retrieval
- Handles citation processing and linking
- Integrates with sentence-based citation system
- Provides efficient querying interfaces

#### JSONStorageService
- Manages persistent storage of lexical values
- Directory Structure:
  - /current: Active lexical value files
  - /versions: Historical versions
  - /backup: Automatic backups
- Features:
  - Automatic versioning
  - Backup creation
  - UTF-8 encoding support
  - Metadata tracking
  - Error handling and logging

### 3. Frontend Components

#### LLMSection
- Enhanced citation display with author/work names
- Integrated sentence context preview modal
- Added version management interface
- Implemented direct citation linking UI

#### CreateForm
- Updated for new citation format
- Added version management controls
- Enhanced metadata input fields
- Improved error handling

#### ResultsDisplay
- Structured lexical value display
- Enhanced citation formatting
- Sentence context preview integration
- Version information display

#### API Integration
- Updated API types for new features
- Enhanced error handling
- Improved TypeScript type safety
- Optimized data fetching

### 4. Models

#### TextDivision
- Enhanced with author_name and work_name fields
- Improved citation formatting
- Links to text_lines for hierarchical access

#### TextLine
- Added sentence_id with unique constraint
- Integrated spaCy token storage
- Direct linking to lexical values

#### LexicalValue
- Updated citation storage format
- Added relationships to text_lines
- Enhanced querying capabilities

## Recent Implementations

### 1. Frontend Integration
- Enhanced citation display system
- Sentence context preview functionality
- Version management interface
- Direct citation linking UI
- Improved TypeScript types
- Fixed hydration issues

### 2. Sentence-Based Citation System
- Added sentence boundary detection
- Implemented full sentence context retrieval
- Enhanced citation formatting with complete sentences
- Optimized queries for sentence-based lookups

### 3. Direct Citation Linking
```sql
-- Key relationships implemented
CREATE TABLE lexical_value_citations (
    lexical_value_id UUID REFERENCES lexical_values(id),
    text_line_id INTEGER REFERENCES text_lines(id),
    context_type VARCHAR(50),
    PRIMARY KEY (lexical_value_id, text_line_id)
);
```

### 4. JSON Storage System
```python
class JSONStorageService:
    """
    Manages JSON storage with:
    - Automatic directory creation
    - Version control
    - Backup management
    - Metadata tracking
    - Error handling
    """
    def __init__(self, base_dir: str = "lexical_values"):
        self.base_dir = Path(base_dir)
        self._ensure_directory_structure()

    # Core operations:
    - save(): Creates/updates lexical value files
    - load(): Retrieves specific versions
    - list_versions(): Tracks file history
    - delete(): Manages file removal
    - get_storage_info(): Reports system status
```

## Database Schema Updates

### Recent Migrations
1. add_sentence_context_to_citations.py
   - Added sentence_id to text_lines
   - Created unique constraints
   - Updated indexes

2. add_direct_citation_links.py
   - Created association tables
   - Added foreign key relationships
   - Implemented efficient indexes

## API Endpoints

### Updated Endpoints
- `/api/lexical/citations`: Now supports sentence-based retrieval
- `/api/lexical/values`: Enhanced with direct citation linking
- `/api/storage/versions`: New endpoint for JSON storage management

## Performance Considerations
- Indexed sentence_id for efficient lookups
- Optimized citation queries
- Efficient JSON storage with versioning
- Proper foreign key relationships
- Optimized frontend rendering
- Improved component hydration

## Next Steps
1. Comprehensive testing of new features
2. Performance monitoring and optimization
3. Documentation updates for new features
4. User acceptance testing

## Technical Debt
- Consider implementing caching layer
- Review index optimization
- Plan for scaling JSON storage
- Monitor frontend performance
- Optimize component re-renders
