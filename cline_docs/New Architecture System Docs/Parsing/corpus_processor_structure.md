# Corpus Processor Architecture

## Overview

The corpus processor has been enhanced with better attribute handling and citation processing, while maintaining its modular structure. Each module handles a specific aspect of text processing, with a clear inheritance hierarchy that builds functionality layer by layer.

## Current Status

### Working Components
1. Modular Structure:
   - Base initialization
   - Component inheritance
   - Error handling
   - Logging

2. Metadata Handling:
   - Extraction from first line
   - Context setting
   - Work structure lookup

### Current Issues
```python
# Line numbers not being extracted
DEBUG:toolkit.migration.line_processor:Created default citation for division 1 line None using structure ['Section', 'line']: {'section': '1'}

Impact:
- Sentences missing line mappings
- Source line IDs incomplete
- Line order potentially incorrect
```

## Work Structure Handling

### Work Structure Flow
```
CitationParser (cached structure lookup)
    └── CorpusProcessor (division structure cache)
        └── Line Processing (structure-aware line numbers)
Example: "0627"."010" -> "De Articulis" -> ["Section", "Line"]

Current Status:
✓ Structure lookup working
✓ Structure caching working
✗ Line number extraction failing
```

## Module Structure

### 1. CorpusBase (corpus_base.py)
- Base initialization and common utilities
- Provides shared resources:
  - SQLAlchemy session
  - SentenceParser
  - CitationParser with structure caching
  - NLPPipeline
- Safe attribute access utilities

### 2. CorpusCitation (corpus_citation.py)
- Inherits from: CorpusBase
- Handles citation parsing and creation
- Key functionalities:
  - Parse citations from line content
  - Create default citations using work structure
  - Handle TLG reference formats
- Current issues:
  ```python
  # Pattern not matching basic citations
  pattern = r"^\.(\d+[a-z]?)\.(\d+[a-z]?)(?:\s|$)"
  # Needs to be fixed to match .1.1, .1.2 etc.
  ```

### 3. CorpusText (corpus_text.py)
- Inherits from: CorpusCitation
- Manages text line and sentence processing
- Key functionalities:
  - Convert database lines to parser lines
  - Handle title vs content line numbering
  - Extract sentence lines and divisions
- Current issues:
  ```python
  # Line numbers not being extracted
  def _get_line_number(self, line):
      structure = self.citation_parser.get_work_structure(
          line.citation.author_id,
          line.citation.work_id
      )
      if structure:
          # Line level found but value missing
          for level in structure:
              if level.lower() == 'line':
                  line_value = citation.hierarchy_levels.get(level.lower())
                  # line_value is None
  ```

### 4. CorpusNLP (corpus_nlp.py)
- Inherits from: CorpusText
- Handles NLP processing and token management
- Key functionalities:
  - Process spaCy documents to dictionary format
  - Extract and manage token categories
  - Map tokens to specific lines
- Impact of current issues:
  - Token mapping may be incorrect
  - Line positions uncertain
  - Context tracking affected

### 5. CorpusDB (corpus_db.py)
- Inherits from: CorpusNLP
- Manages database operations
- Key functionalities:
  - Retrieve work sentences
  - Get sentence analysis
  - Create sentence records
  - Update line analysis and associations
- Impact of current issues:
  - Source line IDs incomplete
  - Line order potentially wrong
  - Analysis mapping affected

### 6. CorpusProcessor (corpus_processor.py)
- Inherits from: CorpusDB
- Main coordinator for text processing
- Key functionalities:
  - Process individual works
  - Process entire corpus
  - Safe attribute handling
  - Structure caching
- Current issues:
  ```python
  # Division structure found but not used properly
  def _get_division_structure(self, division: TextDivision):
      structure = self.citation_parser.get_work_structure(
          division.author_id_field,
          division.work_number_field
      )
      # Structure correct but line numbers not extracted
  ```

## Inheritance Flow

```
CorpusBase (Safe Attribute Access)
    └── CorpusCitation (Structure-Aware Citations)
        └── CorpusText (Structure-Based Line Numbers)
            └── CorpusNLP (Structure in Token Metadata)
                └── CorpusDB (Structure-Aware Storage)
                    └── CorpusProcessor (Structure Caching)
```

## Key Features

1. **Work Structure Handling**
   - ✓ Centralized structure lookup in CitationParser
   - ✓ Multi-level caching (parser and processor)
   - ✗ Structure-aware citation parsing
   - ✗ Structure-based line numbering

2. **Separation of Concerns**
   - ✓ Each module focuses on a specific aspect of processing
   - ✓ Clear boundaries between different functionalities
   - ✓ Safe attribute access throughout

3. **Line Number Handling**
   - ✗ Structure-aware line numbering
   - ✓ Separate tracking of title and content lines
   - ✓ Safe attribute access for line properties

4. **Error Handling**
   - ✓ Safe attribute access with defaults
   - ✓ Detailed logging at each processing stage
   - ✓ Graceful failure handling with fallbacks

## Usage Example

```python
# Initialize processor
processor = CorpusProcessor(
    session=async_session,
    model_path="path/to/spacy/model",
    use_gpu=True
)

# Process a single work
await processor.process_work(work_id=123)

# Process entire corpus
await processor.process_corpus()
```

## Best Practices

1. **Work Structure Handling**
   - Use citation parser's get_work_structure method
   - Leverage structure caching at appropriate levels
   - Use correct levels for line numbers and divisions

2. **Error Handling**
   - Use _get_attr_safe for attribute access
   - Log errors with sufficient context
   - Provide fallback behavior where appropriate

3. **Line Processing**
   - Handle title lines separately from content lines
   - Use work structure for line numbering
   - Safe access to line properties

4. **Database Operations**
   - Use transactions appropriately
   - Batch operations when possible
   - Handle connection issues gracefully

5. **Memory Management**
   - Process works sequentially
   - Clear structure caches between works
   - Monitor memory usage during processing
