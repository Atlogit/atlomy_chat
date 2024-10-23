# CorpusManager User Guide

## Introduction

The CorpusManager is a central component of the Ancient Medical Texts Analysis App, responsible for managing a corpus of ancient medical texts. It provides robust functionality for importing, processing, searching, and managing ancient Greek texts, with special support for TLG format files.

## Features

- Import and process raw text files (TLG and non-TLG formats)
- Store processed texts in an annotated JSONL format
- Retrieve and update existing texts in the corpus
- Advanced search functionality with lemma support
- Integration with lexical value generation
- Comprehensive error handling and logging
- Performance optimizations for large corpora

## Usage

### Initializing CorpusManager

```python
from corpus_manager import CorpusManager

# Initialize with default corpus directory
corpus_manager = CorpusManager()

# Or specify a custom corpus directory
custom_dir = "/path/to/custom/corpus/directory"
corpus_manager = CorpusManager(corpus_dir=custom_dir)
```

### Importing Texts

```python
# Import a TLG format text
corpus_manager.import_text("/path/to/TLG_file.txt")

# Import a non-TLG format text
corpus_manager.import_text("/path/to/other_text_file.txt")

# Check if import was successful
if corpus_manager.text_exists("TLG_file.txt"):
    print("Text successfully imported")
```

### Retrieving Texts

```python
# Get a processed text by its file name
text_data = corpus_manager.get_text("TLG_file.txt")

# Get all texts in the corpus
all_texts = corpus_manager.get_all_texts()

# List text filenames in the corpus
text_list = corpus_manager.list_texts()
```

### Updating Texts

```python
# Update an existing text
updated_data = [{"text": "Updated sentence", "tokens": [], "lemmas": []}]
corpus_manager.update_text("TLG_file.txt", updated_data)

# Save changes to disk
corpus_manager.save_texts()
```

### Removing Texts

```python
# Remove a text from the corpus
corpus_manager.remove_text("text_to_remove.txt")

# Save changes to disk
corpus_manager.save_texts()
```

### Advanced Search

```python
# Search by word
results = corpus_manager.search_texts(word="φλέψ")

# Search by lemma
results = corpus_manager.search_texts(word="φλέψ", search_lemma=True)

# Process search results
for result in results:
    print(f"Text: {result['text_id']}")
    print(f"Sentence: {result['sentence']}")
    print(f"Lemmas: {result['lemmas']}")
    print(f"Context: {result.get('context', '')}")
```

### Integration with Lexical Value Generation

The CorpusManager integrates with the LexicalValueGenerator for creating comprehensive lexical entries:

```python
from lexical_value_generator import LexicalValueGenerator

# Initialize LexicalValueGenerator with CorpusManager
generator = LexicalValueGenerator(corpus_manager)

# Generate lexical value using corpus data
lexical_value = generator.create_lexical_entry("φλέψ", search_lemma=True)
```

## Error Handling and Logging

The CorpusManager includes comprehensive error handling and logging through a centralized logging system:

```python
import logging
from logging_config import setup_logging

# Configure logging
setup_logging()
logger = logging.getLogger(__name__)

try:
    corpus_manager.import_text("nonexistent_file.txt")
except FileNotFoundError as e:
    logger.error(f"File import failed: {e}")
```

Common exceptions:
- `FileNotFoundError`: When trying to import or access a file that doesn't exist
- `json.JSONDecodeError`: When there's an issue parsing the JSONL files
- `OSError`: When there are issues with file system operations
- `ValueError`: When invalid parameters are provided

## Best Practices

1. Always check if a text exists before trying to update or remove it:
```python
if corpus_manager.text_exists("text.txt"):
    corpus_manager.update_text("text.txt", new_data)
```

2. Save changes explicitly after modifications:
```python
corpus_manager.update_text("text.txt", new_data)
corpus_manager.save_texts()  # Persist changes to disk
```

3. Use lemma search for more comprehensive results:
```python
# Search with lemma support for better coverage
results = corpus_manager.search_texts(word="φλέψ", search_lemma=True)
```

4. Handle errors gracefully:
```python
try:
    corpus_manager.import_text("text.txt")
except Exception as e:
    logger.error(f"Import failed: {e}")
    # Implement appropriate error recovery
```

5. Monitor logs for warnings and errors:
```python
# Check logs for issues
logger.info("Starting text import")
corpus_manager.import_text("text.txt")
logger.info("Import completed")
```

## Advanced Usage

### Custom Parsers

The CorpusManager supports custom parsers for different text formats:

1. Create a new parser in the `data_parsing` directory:
```python
# custom_parser.py
def parse_text(text_content):
    # Implement parsing logic
    return parsed_data
```

2. Modify the `import_text` method to use your parser:
```python
if file_extension == ".custom":
    from data_parsing.custom_parser import parse_text
    parsed_data = parse_text(content)
```

### Performance Optimization

For large corpora:

1. Use lemma-based search strategically:
```python
# Only use lemma search when necessary
results = corpus_manager.search_texts(
    word="term",
    search_lemma=specific_lemma_needed
)
```

2. Batch process texts when possible:
```python
# Import multiple texts
for text_file in text_files:
    corpus_manager.import_text(text_file)
corpus_manager.save_texts()  # Save once after all imports
```

3. Implement caching for frequently accessed texts:
```python
from functools import lru_cache

@lru_cache(maxsize=32)
def get_cached_text(text_id):
    return corpus_manager.get_text(text_id)
```

## Integration Examples

### With Lexical Value Generation

```python
# Initialize components
corpus_manager = CorpusManager()
generator = LexicalValueGenerator(corpus_manager)

# Search for term occurrences
results = corpus_manager.search_texts("φλέψ", search_lemma=True)

# Generate lexical value with context
citations = [f"{r['text_id']}: {r['sentence']}" for r in results]
lexical_value = generator.generate_lexical_term("φλέψ", citations)
```

### With TLG Parser

```python
from data_parsing.tlg_parser import TLGParser

# Initialize parser with corpus manager
parser = TLGParser()
corpus_manager.import_text("tlg_text.txt", parser=parser)
```

## Conclusion

The CorpusManager provides a robust and flexible system for managing ancient medical texts, with advanced features for searching, processing, and integrating with other components of the system. Its comprehensive error handling, logging, and performance optimizations make it suitable for both small and large-scale text processing tasks.

For additional support, consult:
- Source code documentation
- Logging output in logs/atlomy_chat.log
- System architecture documentation
- The development team for specific use cases
