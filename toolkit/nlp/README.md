# NLP Pipeline Documentation

## Overview

The NLP Pipeline module provides functionality for processing ancient Greek texts using spaCy, with specific optimizations for handling ancient medical texts. It supports batch processing, category detection, and produces output compatible with our PostgreSQL database schema.

## Components

### NLPPipeline Class

The main class that handles text processing:

```python
from toolkit.nlp.pipeline import NLPPipeline

# Initialize pipeline
pipeline = NLPPipeline(
    model_path="path/to/model",  # Optional: defaults to project model
    batch_size=1000,             # Optional: default batch size
    category_threshold=0.2       # Optional: threshold for category detection
)
```

### Key Features

1. **Text Processing**
   - Handles individual texts or batches
   - Preserves text structure
   - Extracts linguistic features

2. **Token Analysis**
   - Lemmatization
   - Part-of-speech tagging
   - Morphological analysis
   - Category detection

3. **Category Detection**
   - Uses spaCy's span categorization
   - Configurable detection threshold
   - Supports multiple categories per token

## Usage Examples

### Processing Single Texts

```python
# Process a single text
result = pipeline.process_text("ἐγὼ δὲ περὶ μὲν τούτων τῶν θεῶν")

# Result structure
{
    "text": "ἐγὼ δὲ περὶ μὲν τούτων τῶν θεῶν",
    "tokens": [
        {
            "text": "ἐγὼ",
            "lemma": "ἐγώ",
            "pos": "PRON",
            "tag": "Pp1ns---",
            "dep": "nsubj",
            "morph": "{'Case': 'Nom', 'Number': 'Sing', 'Person': '1'}",
            "category": "Body Part"
        },
        # ... more tokens
    ]
}
```

### Batch Processing

```python
# Process multiple texts
texts = [
    "ἐγὼ δὲ περὶ μὲν τούτων",
    "τῶν θεῶν οὐκ οἶδα"
]
results = pipeline.process_batch(texts)
```

### Category Extraction

```python
# Extract unique categories from processed text
categories = pipeline.extract_categories(processed_text)
```

## Configuration

### Model Path

The pipeline uses the project's ancient Greek model by default:
```
assets/models/atlomy_full_pipeline_annotation_131024/model-best
```

You can specify a different model:
```python
pipeline = NLPPipeline(model_path="path/to/custom/model")
```

### Processing Settings

- **batch_size**: Number of texts to process at once (default: 1000)
- **category_threshold**: Minimum confidence for category detection (default: 0.2)

## Integration with Database Loader

The NLP Pipeline output is designed to work seamlessly with the DatabaseLoader:

```python
from toolkit.nlp.pipeline import NLPPipeline
from toolkit.loader.database import DatabaseLoader

# Process text
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

## Error Handling

The pipeline includes comprehensive error handling:
- Model loading errors
- Text processing errors
- Invalid input handling

Example:
```python
try:
    result = pipeline.process_text(text)
except Exception as e:
    logger.error(f"Error processing text: {e}")
```

## Performance Considerations

1. **Batch Processing**
   - Use batch_size appropriate for your memory constraints
   - Default 1000 texts per batch is suitable for most systems
   - Monitor memory usage during large batch operations

2. **Memory Usage**
   - Monitor memory when processing large texts
   - Consider using smaller batch sizes for very large texts
   - Use streaming for extremely large datasets

3. **GPU Acceleration**
   - The pipeline automatically uses GPU if available
   - Configure spaCy to use GPU with `spacy.prefer_gpu()`
   - Monitor GPU memory usage during batch processing

4. **Optimization Tips**
   - Pre-process texts to remove unnecessary whitespace
   - Use appropriate batch sizes for your hardware
   - Consider parallel processing for large datasets
   - Cache frequently accessed results

## Testing

Comprehensive tests are available in `toolkit/tests/test_nlp_pipeline.py`:
- Pipeline initialization
- Text processing
- Batch processing
- Category extraction
- Error handling

## Integration with Text Processing Toolkit

The NLP Pipeline is designed to work with other components of the Text Processing Toolkit:

1. **Citation Parser Integration**
   ```python
   from toolkit.parsers.citation import CitationParser
   from toolkit.nlp.pipeline import NLPPipeline

   # Parse citations and process text
   citation_parser = CitationParser()
   nlp_pipeline = NLPPipeline()

   text = "[0057][001][1][2] Some Greek text..."
   remaining, citation = citation_parser.parse_citation(text)
   processed = nlp_pipeline.process_text(remaining)
   ```

2. **Text Parser Integration**
   ```python
   from toolkit.parsers.text import TextParser
   from toolkit.nlp.pipeline import NLPPipeline

   # Extract and process text
   text_parser = TextParser()
   nlp_pipeline = NLPPipeline()

   lines = await text_parser.parse_file("text.txt")
   processed_lines = [
       nlp_pipeline.process_text(line.content)
       for line in lines
   ]
   ```

3. **Sentence Parser Integration**
   ```python
   from toolkit.parsers.sentence import SentenceParser
   from toolkit.nlp.pipeline import NLPPipeline

   # Process sentences
   sentence_parser = SentenceParser()
   nlp_pipeline = NLPPipeline()

   sentences = await sentence_parser.parse_lines(lines)
   processed_sentences = nlp_pipeline.process_batch(
       [sentence.content for sentence in sentences]
   )
   ```

## Advanced Features

### Custom Category Detection

You can customize category detection by adjusting the threshold:

```python
pipeline = NLPPipeline(category_threshold=0.3)  # More strict
```

### Morphological Analysis

Access detailed morphological information:

```python
result = pipeline.process_text("τῶν θεῶν")
morph = result["tokens"][0]["morph"]
print(morph)  # {'Case': 'Gen', 'Number': 'Plur'}
```

### Dependency Parsing

Analyze syntactic relationships:

```python
result = pipeline.process_text("ἐγὼ δὲ περὶ μὲν τούτων")
for token in result["tokens"]:
    print(f"{token['text']} -> {token['dep']}")
```

## Maintenance and Updates

### Model Updates

To update the spaCy model:

1. Download new model:
   ```bash
   python -m spacy download grc_dep_treebanks_trf
   ```

2. Update model path:
   ```python
   pipeline = NLPPipeline(
       model_path="path/to/new/model"
   )
   ```

### Performance Monitoring

Monitor pipeline performance:

```python
import time

start = time.time()
results = pipeline.process_batch(large_text_batch)
duration = time.time() - start

print(f"Processed {len(large_text_batch)} texts in {duration:.2f} seconds")
```

### Logging

The pipeline uses Python's logging module:

```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Logs will show pipeline operations
pipeline = NLPPipeline()
```

## Future Enhancements

Planned improvements:

1. **Streaming Support**
   - Process very large texts in chunks
   - Reduce memory usage
   - Support for continuous processing

2. **Additional Language Models**
   - Support for Latin texts
   - Support for Arabic texts
   - Custom model training pipeline

3. **Performance Optimizations**
   - Parallel processing improvements
   - Better memory management
   - GPU optimization

4. **Enhanced Category Detection**
   - More granular categories
   - Custom category training
   - Confidence scoring

## Contributing

To contribute to the NLP Pipeline:

1. Follow the project's coding standards
2. Add tests for new features
3. Update documentation
4. Submit pull requests with clear descriptions

## Support

For issues and questions:

1. Check the documentation
2. Review test cases for examples
3. Submit detailed bug reports
4. Contact the development team

## License

This module is part of the Ancient Medical Texts Analysis project and is subject to the project's licensing terms.
