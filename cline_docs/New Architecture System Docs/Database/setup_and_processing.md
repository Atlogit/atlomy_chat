# Database Setup and Text Processing Guide

## Overview
This guide details the steps for setting up the PostgreSQL database and processing texts through the NLP pipeline for the Ancient Medical Texts Analysis project.

## Components Available

1. **Database Configuration**
   - Located in `app/core/database.py`
   - Uses SQLAlchemy with async support
   - Default connection URL: `postgresql+asyncpg://postgres:postgres@localhost/ancient_texts_db`
   - Configurable through environment variables

2. **Database Schema**
   - Defined in Alembic migrations (`alembic/versions/`)
   - Tables:
     - authors
     - texts
     - text_divisions
     - text_lines
     - lemmas
     - lemma_analyses

3. **Processing Tools**
   - **Database Loader** (`toolkit/loader/database.py`)
     - Handles text storage in PostgreSQL
     - Supports individual and bulk loading
     - Manages relationships between entities
   
   - **Corpus Processor** (`toolkit/migration/process_corpus.py`)
     - Coordinates text processing through NLP pipeline
     - Supports parallel processing
     - Includes progress tracking and logging

## Setup Steps

1. **Environment Configuration**
   ```bash
   # Create .env file with required settings
   cp .env.example .env
   
   # Required additions to .env:
   DATABASE_URL=postgresql+asyncpg://username:password@host/dbname
   ```

2. **Database Creation**
   ```bash
   # Create PostgreSQL database
   createdb ancient_texts_db  # Or your chosen database name
   
   # Run Alembic migrations
   alembic upgrade head
   ```

3. **Text Processing Setup**
   - Ensure texts are in a designated directory
   - Configure CORPUS_DIR in .env to point to text directory
   - Optional: Configure NLP model path

## Processing Workflow

1. **Basic Processing**
   ```bash
   python -m toolkit.migration.process_corpus
   ```

2. **Advanced Processing Options**
   ```bash
   # Parallel processing with custom batch size
   python -m toolkit.migration.process_corpus --parallel --batch-size 200
   
   # Specify custom model path
   python -m toolkit.migration.process_corpus --model-path /path/to/model
   
   # Control worker processes
   python -m toolkit.migration.process_corpus --parallel --max-workers 4
   ```

## Monitoring and Logging

- Logs are written to the configured log file
- Progress can be monitored through log output
- Processing status includes completion percentage
- Error handling with detailed logging

## Database Loader Usage

The DatabaseLoader class provides methods for storing processed texts in PostgreSQL. Here's how to use it:

### 1. Basic Text Loading

```python
from toolkit.loader.database import DatabaseLoader
from app.core.database import async_session

async with async_session() as session:
    loader = DatabaseLoader(session)
    
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
    
    # Load text into database
    text = await loader.load_text(**text_data)
```

### 2. Bulk Loading Multiple Texts

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

# Bulk load texts
texts = await loader.bulk_load_texts(texts_data)
```

### 3. Updating Text Categories

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

### Key Features

1. **Author Management**
   - Automatically creates or retrieves authors
   - Supports language code specification (default: "grc" for ancient Greek)

2. **Text Structure**
   - Handles hierarchical text divisions (books, chapters, sections)
   - Stores page numbers and metadata
   - Manages line content and numbering

3. **NLP Data**
   - Stores spaCy token data in JSONB format
   - Maintains token categories for efficient querying
   - Supports category updates and modifications

4. **Error Handling**
   - Automatic transaction rollback on errors
   - Detailed error logging
   - Data integrity protection

### Data Structure Requirements

1. **Text Data Format**
   ```python
   {
       "author_name": str,          # Required
       "text_title": str,           # Required
       "reference_code": str,       # Required
       "language_code": str,        # Optional (default: "grc")
       "divisions": [               # Required
           {
               "book_number": str,      # Optional
               "chapter_number": str,    # Optional
               "section_number": str,    # Optional
               "page_number": int,       # Optional
               "metadata": dict,         # Optional
               "lines": [               # Required
                   {
                       "line_number": int,   # Optional
                       "content": str,       # Required
                       "nlp_data": {         # Required
                           "tokens": [...]   # Required
                       }
                   }
               ]
           }
       ]
   }
   ```

2. **NLP Token Format**
   ```python
   {
       "text": str,        # Original token text
       "lemma": str,       # Lemmatized form
       "pos": str,         # Part of speech
       "category": str     # Token category (comma-separated)
   }
   ```

### Best Practices

1. **Transaction Management**
   - Always use async context manager for sessions
   - Let the loader handle transaction commits/rollbacks
   - Don't mix manual commits with loader operations

2. **Bulk Operations**
   - Use bulk_load_texts for multiple texts
   - Prepare complete data structures before loading
   - Handle errors at the appropriate level

3. **Category Updates**
   - Batch category updates when possible
   - Include complete token data with updates
   - Verify line IDs before updating

4. **Error Recovery**
   - Log operation IDs for tracking
   - Implement retry logic for transient failures
   - Maintain data backup strategies

5. **Check Database**

use code to check if content ofdatabase:
python3 -c "
from app.core.database import async_session
import asyncio
from sqlalchemy import select
from app.models.text import Text

async def check_texts():
    async with async_session() as session:
        result = await session.execute(select(Text))
        texts = result.scalars().all()
        print(f'Found {len(texts)} existing texts in database')

asyncio.run(check_texts())
"
