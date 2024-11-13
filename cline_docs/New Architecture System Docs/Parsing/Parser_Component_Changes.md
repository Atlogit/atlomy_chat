# Parser Component Changes and Improvements

## Overview

This document details the changes made to improve the parser components and processing pipeline, focusing on singleton patterns, shared resources, and proper inheritance chains.

## Component Architecture

### Singleton Components

1. SharedParsers
```python
class SharedParsers:
    _instance = None
    
    @property
    def sentence_utils(self):
        # Lazy loading
        if self._sentence_utils is None:
            self._sentence_utils = SentenceUtils.get_instance()
        return self._sentence_utils
    
    @property
    def citation_parser(self):
        # Lazy loading
        if self._citation_parser is None:
            self._citation_parser = CitationParser.get_instance()
        return self._citation_parser
```

2. SentenceParser
```python
class SentenceParser:
    _instance = None
    
    def __init__(self):
        if SentenceParser._instance is not None:
            raise RuntimeError("Use get_instance() to access SentenceParser")
        # Get shared components
        shared = SharedParsers.get_instance()
        self.utils = shared.sentence_utils
        self.citation_parser = shared.citation_parser
```

3. CitationParser
```python
class CitationParser:
    _instance = None
    
    def __init__(self):
        if CitationParser._instance is not None:
            raise RuntimeError("Use get_instance() to access CitationParser")
```

### Inheritance Chain

```
CorpusBase (uses SharedComponents)
└── CorpusCitation (citation handling)
    └── CorpusText (text processing)
        └── CorpusNLP (NLP processing)
            └── CorpusDB (database operations)
                └── CorpusProcessor (coordination)
```

## Processing Pipeline

### 1. Text Processing (CorpusText)

```python
def process_lines(self, db_lines: List[DBTextLine], division: TextDivision) -> List[ParserTextLine]:
    # Extract citation and content
    citation_text, content = self._extract_citation_text(line.content)
    
    # Parse citation if found
    if citation_text:
        _, citations = self.parse_citation(
            citation_text,
            division.author_id_field,
            division.work_number_field
        )
        if citations:
            citation = citations[0]
            structure = self._get_division_structure(
                division.author_id_field,
                division.work_number_field
            )
            line_number = self._get_line_number_from_citation(citation, structure)
```

### 2. Sentence Formation (SentenceParser)

```python
def parse_lines(self, lines: List[TextLine]) -> List[Sentence]:
    # Parse sentences from line content
    line_sentences = self._parse_line_content(line, content)
    
    # Build sentences with proper citation context
    sentences.append(Sentence(
        content=''.join(current_sentence),
        source_lines=source_lines,
        citation=current_citation,
        structure=current_structure
    ))
```

### 3. NLP Processing (CorpusNLP)

```python
def process_sentence(self, sentence: Sentence) -> Optional[Dict[str, Any]]:
    # Process with spaCy
    doc = self.nlp_pipeline.nlp(sentence.content)
    processed_doc = self._process_doc_to_dict(doc)
    
    # Map tokens to lines
    line_analysis = self._map_tokens_to_line(
        db_line.content,
        processed_doc
    )
```

## Line Number Extraction

### Citation-based Line Numbers
```python
def _get_line_number_from_citation(self, citation: Citation, structure: List[str]) -> Optional[int]:
    # Handle title citations
    if citation.title_number:
        try:
            return int(citation.title_number)
        except (ValueError, TypeError):
            return None
            
    # Find line level in structure
    for level in structure:
        if level.lower() == 'line':
            line_value = citation.hierarchy_levels.get(level.lower())
            if line_value:
                try:
                    # Extract numeric part if there's an alpha suffix
                    match = re.match(r'(\d+)[a-z]?', line_value)
                    if match:
                        return int(match.group(1))
                except (ValueError, TypeError):
                    pass
    return None
```

## Database Transaction Handling

### Work-level Transactions
```python
async def process_work(self, work_id: int, pbar: Optional[tqdm] = None) -> None:
    async with self.session.begin_nested():
        try:
            # Process divisions
            for division in divisions:
                await self.process_division(division)
            await self.session.commit()
            logger.info("Committed changes for work %d", work_id)
        except Exception as e:
            await self.session.rollback()
            logger.error("Error processing work %d: %s", work_id, str(e))
```

### Division-level Error Handling
```python
async def process_division(self, division: TextDivision) -> None:
    try:
        # Process lines
        db_lines = await self.get_division_lines(division.id)
        parser_lines = self.process_lines(db_lines, division)
        
        # Process sentences
        sentences = self.parse_sentences(parser_lines)
        for sentence in sentences:
            await self.process_sentence_with_nlp(sentence, db_lines)
            
    except Exception as e:
        logger.error("Error processing division %d: %s", division.id, str(e))
        # Continue with next division
```

## Progress Tracking

### Work-based Progress
```python
async def process_corpus(self) -> None:
    works = await self.get_work_list()
    with tqdm(total=len(works), desc="Processing corpus", unit="work") as pbar:
        for work in works:
            await self.process_work(work.id, pbar)
            pbar.update(1)
```

### Detailed Progress Logging
```python
logger.info("Starting sequential processing of %d works", total_works)
logger.info("Processing division %d (chapter %s)", division.id, division.chapter)
logger.debug("Processed %d lines into %d parser lines", len(db_lines), len(parser_lines))
```

## Key Improvements

1. Singleton Pattern Implementation
   - Prevents multiple instances of shared components
   - Lazy loading to avoid circular dependencies
   - Proper state management

2. Citation Processing
   - Improved line number extraction from citations
   - Better structure handling
   - Proper citation inheritance in sentences

3. NLP Processing
   - Robust token mapping
   - Better error handling
   - Improved line analysis

4. Progress Tracking
   - Work-based progress tracking
   - Clear progress indication
   - Better error reporting

5. Transaction Management
   - Work-level transactions
   - Division-level error isolation
   - Proper rollback handling

## Usage Example

```python
# Get shared components (lazy loaded)
shared = SharedParsers.get_instance()
parser = shared.sentence_parser
citation = shared.citation_parser

# Process corpus
processor = CorpusProcessor(session)
await processor.process_corpus()
```

## Error Handling

1. Component Initialization
```python
if cls._instance is not None:
    raise RuntimeError("Use get_instance() to access component")
```

2. NLP Processing
```python
try:
    doc = self.nlp_pipeline.nlp(sentence.content)
    if not doc or not doc.text:
        logger.error("Failed to process sentence")
        return None
except Exception as e:
    logger.error("Error processing sentence: %s", str(e))
    return None
```

3. Token Mapping
```python
try:
    line_tokens = []
    line_start = 0
    for token in processed_doc['tokens']:
        pos = line_text.find(token['text'], line_start)
        if pos >= 0:
            line_tokens.append(token)
except Exception as e:
    logger.error("Error mapping tokens: %s", str(e))
    return None
```

## Logging

Improved logging throughout the system:
```python
logger.debug("Extracted line number %s from citation %s", 
             line_number, citation_text)
logger.debug("Found %d database lines for sentence: %s", 
             len(sentence_lines), sentence.content[:100])
logger.error("Error processing division %d: %s", 
             division.id, str(e))
