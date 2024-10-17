# CorpusManager User Guide

## Introduction

The CorpusManager is a central component of the Ancient Medical Texts Analysis App, responsible for managing a corpus of ancient medical texts. This guide provides an overview of its functionality and usage.

## Features

- Import and process raw text files (TLG and non-TLG formats)
- Store processed texts in an annotated JSONL format
- Retrieve and update existing texts in the corpus
- Search across multiple texts using regular expressions
- Robust error handling and logging

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
```

### Retrieving Texts

```python
# Get a processed text by its file name
text_data = corpus_manager.get_text("TLG_file.txt")

# List all texts in the corpus
all_texts = corpus_manager.list_texts()
```

### Updating Texts

```python
# Update an existing text
updated_data = [{"text": "Updated sentence", "tokens": []}]
corpus_manager.update_text("TLG_file.txt", updated_data)
```

### Removing Texts

```python
# Remove a text from the corpus
corpus_manager.remove_text("text_to_remove.txt")
```

### Searching Texts

```python
# Search across all texts in the corpus
search_results = corpus_manager.search_texts("example query")

# Process search results
for result in search_results:
    print(f"Text: {result['text_id']}, Sentence: {result['sentence'][:50]}...")
```

## Error Handling

The CorpusManager includes comprehensive error handling and logging. Common exceptions you might encounter include:

- `FileNotFoundError`: When trying to import or access a file that doesn't exist
- `json.JSONDecodeError`: When there's an issue parsing the JSONL files
- `OSError`: When there are issues with file system operations

All operations are logged, with errors logged at the ERROR level for easy debugging.

## Best Practices

1. Always check if a text exists before trying to update or remove it.
2. Regularly save the corpus to ensure all changes are persisted to disk.
3. Use try-except blocks when calling CorpusManager methods to handle potential exceptions gracefully.
4. Monitor the logs for any warnings or errors during operation.

## Advanced Usage

### Custom Parsers

The CorpusManager uses different parsers for TLG and non-TLG texts. If you need to add support for a new text format:

1. Create a new parser in the `data_parsing` directory.
2. Modify the `import_text` method in CorpusManager to use your new parser for the appropriate file type.

### Performance Optimization

For large corpora, consider:

1. Implementing a caching mechanism to reduce disk I/O.
2. Using parallel processing for operations like searching or batch importing.

## Conclusion

The CorpusManager provides a robust and flexible system for managing ancient medical texts. By following this guide, you should be able to effectively use its features in your project. For any additional questions or advanced usage scenarios, please refer to the source code or contact the development team.
