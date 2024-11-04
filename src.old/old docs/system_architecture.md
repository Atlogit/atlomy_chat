# System Architecture: Ancient Medical Texts Analysis App

## Overview
The system provides a comprehensive solution for analyzing ancient medical texts, with robust text processing, lexical value generation, and advanced search capabilities. The architecture emphasizes modularity, performance, and extensibility, with recent additions including caching mechanisms, web interface, and preparation for parallel processing.

## Core Components

### 1. Web Interface
- **Frontend** (`src/static/`)
  - Modern, responsive web interface
  - Three main sections:
    - LLM Assistant for text queries
    - Lexical Value management
    - Corpus Manager interface
  - Components:
    - `index.html`: Main interface structure
    - `styles.css`: Responsive styling
    - `app.js`: Client-side logic

- **Backend API** (`src/api.py`)
  - FastAPI application
  - RESTful endpoints for all core functionality
  - Static file serving
  - Error handling and logging
  - Integrates with core components

### 2. Corpus Management System
- **CorpusManager** (`src/corpus_manager.py`)
  - Manages text corpus with JSONL storage
  - Provides advanced search with lemma support
  - Integrates with lexical value generation
  - Implements efficient text retrieval
  - Methods:
    - `import_text`: Process and store new texts
    - `search_texts`: Search with lemma support
    - `get_text`: Retrieve processed texts
    - `save_texts`: Persist changes to disk

### 3. Text Processing Pipeline
- **TLGParser** (`src/data_parsing/tlg_parser.py`)
  - Processes TLG format texts
  - Extracts references and citations
  - Converts to annotated JSONL
  - Uses relative imports for modularity

- **Specialized Parsers**
  - Galenus parser (`src/data_parsing/galenus/galenus_parsing.py`)
  - Hippocrates parser (`src/data_parsing/hipocrates_sacred_disease/hippocrates_parsing.py`)

### 4. Lexical Value System
- **LexicalValueGenerator** (`src/lexical_value_generator.py`)
  - Generates lexical entries using Claude-3
  - Implements caching for performance
  - Supports batch processing
  - Preparing for parallel processing
  - Methods:
    - `create_lexical_entry`: Generate new entries
    - `get_citations`: Extract relevant citations
    - `query_llm`: Interface with Claude-3

- **LexicalValueStorage** (`src/lexical_value_storage.py`)
  - Manages persistent storage
  - Implements version history
  - Handles cache operations
  - Methods:
    - `store`: Save lexical values
    - `retrieve`: Get cached or stored values
    - `get_version_history`: Track changes

- **LexicalValueCLI** (`src/lexical_value_cli.py`)
  - Provides command-line interface
  - Supports CRUD operations
  - Enables version management
  - Collects user feedback

### 5. Caching System
```python
class CacheManager:
    def __init__(self, max_size=1000, expiration=3600):
        self._cache = {}
        self._max_size = max_size
        self._expiration = expiration
        self._lock = threading.Lock()

    def get(self, key):
        with self._lock:
            if key in self._cache:
                value, timestamp = self._cache[key]
                if time.time() - timestamp < self._expiration:
                    return value
        return None

    def set(self, key, value):
        with self._lock:
            self._cache[key] = (value, time.time())
            if len(self._cache) > self._max_size:
                self._evict_oldest()
```

### 6. Logging System
- **LoggingConfig** (`src/logging_config.py`)
  - Centralized logging configuration
  - JSON-formatted logs
  - Dynamic log level adjustment
  - Console and file outputs

## Data Flow

1. Web Interface Flow:
```
User Request → FastAPI Backend → Core Components → JSON Response → UI Update
```

2. Text Processing Flow:
```
Raw Text → TLGParser → Annotated JSONL → CorpusManager
```

3. Lexical Value Generation Flow:
```
Search Request → Cache Check → LLM Generation → Storage
```

4. Parallel Processing Flow (Planned):
```
Batch Request → Worker Pool → Parallel Generation → Result Aggregation
```

## API Endpoints

### 1. LLM Assistant
```
POST /api/llm/query
- Query ancient medical texts
- Returns processed results with citations
```

### 2. Lexical Values
```
POST   /api/lexical/create    - Create new lexical entry
GET    /api/lexical/get/{id} - Retrieve entry
GET    /api/lexical/list     - List all entries
PUT    /api/lexical/update   - Update entry
DELETE /api/lexical/delete   - Delete entry
```

### 3. Corpus Manager
```
GET  /api/corpus/list   - List available texts
POST /api/corpus/search - Search texts
GET  /api/corpus/all    - Get all texts
```

## Planned Parallel Processing Architecture

### 1. Worker Pool Management
```python
class LexicalValueWorkerPool:
    def __init__(self, num_workers=4):
        self.pool = ProcessPoolExecutor(max_workers=num_workers)
        self.cache = ThreadSafeCache()

    async def process_batch(self, terms):
        futures = [
            self.pool.submit(self._generate_value, term)
            for term in terms
        ]
        return await asyncio.gather(*futures)

    def _generate_value(self, term):
        if cached := self.cache.get(term):
            return cached
        value = self.generator.create_lexical_entry(term)
        self.cache.set(term, value)
        return value
```

### 2. Thread-Safe Cache
```python
class ThreadSafeCache:
    def __init__(self):
        self._cache = {}
        self._lock = Lock()

    def get(self, key):
        with self._lock:
            return self._cache.get(key)

    def set(self, key, value):
        with self._lock:
            self._cache[key] = value
```

### 3. Performance Monitoring
```python
class PerformanceMonitor:
    def __init__(self):
        self.metrics = defaultdict(list)
        self._lock = Lock()

    def record_metric(self, operation, duration):
        with self._lock:
            self.metrics[operation].append(duration)

    def get_statistics(self):
        return {
            op: {
                'avg': mean(durations),
                'max': max(durations),
                'min': min(durations)
            }
            for op, durations in self.metrics.items()
        }
```

## Integration Points

### 1. LLM Integration
- AWS Bedrock (Claude-3) for generation
- Configurable model selection
- Error handling and retries
- Cost optimization

### 2. Storage Integration
- File-based JSON storage
- Version history tracking
- Cache management
- Backup mechanisms

### 3. Web Interface Integration
- FastAPI backend
- RESTful API endpoints
- Static file serving
- Error handling and logging

## Error Handling

1. Custom Exceptions:
```python
class LexicalValueError(Exception): pass
class CacheError(Exception): pass
class StorageError(Exception): pass
class APIError(Exception): pass
```

2. Error Recovery:
```python
def safe_generate(self, term, retries=3):
    for attempt in range(retries):
        try:
            return self.generate_value(term)
        except LexicalValueError as e:
            logger.error(f"Attempt {attempt + 1} failed: {e}")
            if attempt == retries - 1:
                raise
```

## Testing Strategy

### 1. Unit Tests
- Component-level testing
- Mock external dependencies
- Error case coverage
- Performance benchmarks

### 2. Integration Tests
- Cross-component functionality
- End-to-end workflows
- API endpoint testing
- UI integration testing

### 3. Performance Tests
- Load testing
- Concurrency testing
- Cache efficiency
- Resource utilization

## Future Enhancements

1. Web Interface
- Advanced search interface
- Real-time updates
- Interactive visualizations
- Batch operations UI

2. Parallel Processing
- Worker pool implementation
- Load balancing
- Resource management
- Performance monitoring

3. Advanced Caching
- Distributed caching
- Cache preloading
- Intelligent eviction
- Cache analytics

4. Feedback System
- Quality metrics
- Automated improvements
- User feedback integration
- Version control

5. Monitoring
- Performance metrics
- Resource utilization
- Error tracking
- Usage analytics

This architecture provides a robust foundation for the Ancient Medical Texts Analysis App, with a modern web interface and clear paths for implementing parallel processing and other planned enhancements while maintaining system reliability and performance.
