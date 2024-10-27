# Text Processing Toolkit Architecture

## Purpose
The Text Processing Toolkit handles the ingestion and processing of new texts, managing the conversion from raw text to structured database entries.

## Component Structure

text_processing_toolkit/
├── processors/
│ ├── citation_parser.py # [0057] format handling
│ ├── text_processor.py # Text cleaning and structuring
│ ├── nlp_processor.py # spaCy pipeline
│ └── reference_resolver.py # Cross-reference handling
├── importers/
│ ├── coda_importer.py # Import from Coda tables
│ ├── json_importer.py # Import from JSON/JSONL
│ └── elastic_importer.py # Import from Elasticsearch
├── db/
│ ├── models.py # SQLAlchemy models
│ ├── migrations/ # Alembic migrations
│ └── loader.py # Database operations
└── utils/
├── validators.py # Data validation
└── parallel_handler.py # Early/modern parallel handling


## Key Features
1. **Text Processing**
   - Citation parsing
   - Text cleaning
   - Structure extraction
   - Parallel text handling

2. **NLP Processing**
   - spaCy pipeline integration
   - Custom model support
   - Span categorization
   - Token attribution

3. **Data Import**
   - Coda table import
   - JSON/JSONL processing
   - Elasticsearch data migration

4. **Database Operations**
   - Schema management
   - Data validation
   - Batch operations
   - Migration handling

## Usage Examples

### Basic Text Processing
```python
from text_processing_toolkit import TextProcessor

processor = TextProcessor()
result = await processor.process_file(
    "new_text.txt",
    edition_type="modern"
)
```

## Coda Import/export

TBD

## NLP Processing

from text_processing_toolkit import NLPProcessor

nlp = NLPProcessor()
doc = await nlp.process_text(text)
spans = nlp.extract_categories(doc)

## Configuration

The toolkit uses a YAML configuration file:

processing:
  batch_size: 1000
  nlp_model: "grc_spacy_model"
  parallel_workers: 4

database:
  url: "postgresql+asyncpg://user:pass@localhost/db"
  pool_size: 20

nlp:
  model_path: "path/to/model"
  categories: ["Body Part", "Disease", "Treatment"]

## Next Steps

Review the Database Schema
Understand the Migration Strategy
Follow the Implementation Guide

