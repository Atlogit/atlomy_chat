# Database Loader Documentation

## Overview

The Database Loader module provides functionality for storing processed ancient texts in PostgreSQL, handling the complex relationships between authors, texts, divisions, and lines. It supports both individual text loading and bulk operations.

## Components

### DatabaseLoader Class

The main class that handles database operations:

```python
from toolkit.loader.database import DatabaseLoader
from sqlalchemy.ext.asyncio import AsyncSession

# Initialize loader with async session
loader = DatabaseLoader(session: AsyncSession)
```

### Key Features

1. **Text Loading**
   - Handles author creation/lookup
   - Manages text hierarchies
   - Stores NLP analysis data

2. **Bulk Operations**
   - Efficient batch loading
   - Transaction management
   - Error handling and rollback

3. **Category Management**
   - Updates text categories
   - Maintains category arrays
   - Preserves NLP token data

## Usage Examples

### Loading Individual Texts

```python
# Prepare text data
text_data = {
    "author_name": "Hippocrates",
    "text_title": "On Ancient Medicine",
    "reference_code": "[0057]",
    "divisions": [
        {
            "book_number": "1",
            "chapter_number": "2",
            "section_number": "3",
            "page_number": 42,
            "metadata": {"source": "TLG"},
            "lines": [
                {
                    "line_number": 1,
                    "content": "ἐγὼ δὲ περὶ μὲν τούτων",
                    "nlp_data": {
                        "tokens": [
                            {
                                "text": "ἐγὼ",
                                "lemma": "ἐγώ",
                                "pos": "PRON",
                                "category": "Body Part"
                            }
                        ]
                    }
                }
            ]
        }
    ]
}

# Load text
text = await loader.load_text(**text_data)
```

### Bulk Loading

```python
# Prepare multiple texts
texts_data = [
    {
        "author_name": "Hippocrates",
        "title": "On Ancient Medicine",
        "reference_code": "[0057]",
        "divisions": [...]
    },
    {
        "author_name": "Galen",
        "title": "On the Natural Faculties",
        "reference_code": "[0058]",
        "divisions": [...]
    }
]

# Bulk load
texts = await loader.bulk_load_texts(texts_data)
```

### Updating Categories

```python
# Update categories for specific lines
updates = [
    {
        "line_id": 1,
        "categories": ["Body Part", "Topography"],
        "nlp_data": {
            "tokens": [
                {
                    "text": "ἐγὼ",
                    "category": "Body Part, Topography"
                }
            ]
        }
    }
]

await loader.update_text_categories(text_id=1, line_updates=updates)
```

## Database Schema Integration

The loader works with the following models:

1. **Author**
   - Name and language information
   - One-to-many relationship with texts

2. **Text**
   - Title and reference information
   - Metadata in JSONB format
   - One-to-many relationship with divisions

3. **TextDivision**
   - Hierarchical structure (book, chapter, section)
   - Page numbers and metadata
   - One-to-many relationship with lines

4. **TextLine**
   - Content and line numbers
   - NLP analysis data in JSONB format
   - Category arrays for efficient querying

## Error Handling

The loader includes comprehensive transaction management:

```python
try:
    await loader.load_text(**text_data)
except Exception as e:
    # Automatic rollback on error
    logger.error(f"Error loading text: {e}")
```

## Performance Optimization

1. **Batch Loading**
   - Use bulk_load_texts for multiple texts
   - Efficient transaction management
   - Reduced database round trips

2. **Category Updates**
   - Batch category updates
   - Efficient JSONB operations
   - Minimal data transfer

3. **Connection Management**
   - Connection pooling support
   - Async operations
   - Transaction optimization

## Validation

The loader performs several validations:

1. **Data Integrity**
   - Required fields presence
   - Reference format validation
   - Relationship consistency

2. **Content Validation**
   - Text content presence
   - Valid NLP data structure
   - Category format validation

3. **Relationship Validation**
   - Author existence
   - Text hierarchy consistency
   - Line number sequence

## Testing

Comprehensive tests are available in `toolkit/tests/test_database_loader.py`:
- Text loading
- Bulk operations
- Category updates
- Error handling
- Transaction management

## Integration with NLP Pipeline

The loader is designed to work seamlessly with the NLP Pipeline:

```python
from toolkit.nlp.pipeline import NLPPipeline
from toolkit.loader.database import DatabaseLoader

# Process text with NLP pipeline
pipeline = NLPPipeline()
processed = pipeline.process_text(text_content)

# Prepare for database
text_data = {
    "author_name": "Hippocrates",
    "text_title": "On Ancient Medicine",
    "reference_code": "[0057]",
    "divisions": [{
        "lines": [{
            "content": processed["text"],
            "nlp_data": processed
        }]
    }]
}

# Load into database
loader = DatabaseLoader(session)
await loader.load_text(**text_data)
```

## Migration Support

The loader supports data migration scenarios:

1. **Incremental Loading**
   - Load texts progressively
   - Track loading progress
   - Handle interruptions

2. **Data Updates**
   - Update existing records
   - Preserve relationships
   - Maintain data integrity

3. **Validation Rules**
   - Configure validation requirements
   - Handle legacy data
   - Maintain consistency
