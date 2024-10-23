# Project Context: Ancient Medical Texts Analysis App

## Quick Start Guide for LLM-Coder

1. **Current Status**: Web Interface Debugged and Operational
   - Fixed static file serving configuration
   - Corrected logger initialization
   - Verified component initialization
   - Confirmed API endpoint functionality
   - Ready for parallel processing implementation

2. **Next Steps**:
   a. Implement parallel processing architecture
      - Design thread-safe data structures
      - Create worker pool management
      - Implement load balancing
      - Add performance monitoring
   b. Enhance feedback system
      - Design feedback collection interface
      - Create quality metrics framework
      - Implement feedback integration pipeline
      - Add automated improvement suggestions
   c. Expand testing framework
      - Add parallel processing tests
      - Create performance benchmarks
      - Implement stress testing
      - Add integration tests

3. **Key Files to Review**:
   - `/app/api.py`: FastAPI application with endpoint definitions
   - `/static/`: Frontend files (index.html, styles.css, app.js)
   - `/src/lexical_value_generator.py`: Core generation functionality
   - `/src/lexical_value_storage.py`: Storage and caching system
   - `/src/corpus_manager.py`: Text management and search
   - `/src/logging_config.py`: Centralized logging system
   - `/tests/test_lexical_value_generator.py`: Unit tests

4. **Tech Stack Highlights**:
   - Python 3.x with multiprocessing
   - FastAPI for web API
   - AWS Bedrock (Claude-3) for LLM
   - spaCy for NLP
   - Custom caching system
   - JSON/JSONL for data storage
   - Comprehensive logging system
   - pytest for testing

5. **Recent Updates**:
   - Fixed static file serving in web interface
   - Corrected logger initialization
   - Verified component initialization
   - Confirmed API endpoint functionality
   - Updated documentation
   - Organized static files properly

6. **Project Structure**:
   - `/app/`: API and server configuration
   - `/static/`: Frontend files
   - `/src/`: Core application code
   - `/tests/`: Test suites
   - `/cline_docs/`: Documentation
   - `/logs/`: Log files
   - `/data_parsing/`: Text parsers

7. **Key Considerations**:
   - Thread safety in parallel processing
   - Cache consistency across processes
   - Performance monitoring and optimization
   - Error handling in distributed operations
   - Data integrity in concurrent operations
   - Test coverage for parallel scenarios
   - Documentation of concurrent patterns

8. **Development Guidelines**:
   - Follow test-driven development
   - Maintain comprehensive documentation
   - Use centralized logging
   - Ensure thread safety
   - Monitor performance metrics
   - Handle errors gracefully
   - Keep code modular and extensible

9. **Getting Started**:
   - Server runs on http://localhost:8000
   - API documentation at /docs
   - Static files served from /static
   - Logging configured via environment variables
   - Hot reloading enabled for development

## Implementation Notes

### Parallel Processing Design

1. Worker Pool Management:
```python
from multiprocessing import Pool

def process_batch(batch):
    # Process lexical values in parallel
    with Pool() as pool:
        results = pool.map(generate_lexical_value, batch)
    return results
```

2. Thread-Safe Caching:
```python
from threading import Lock

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

3. Performance Monitoring:
```python
import time

def monitor_performance(func):
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start
        logger.info(f"Operation took {duration:.2f} seconds")
        return result
    return wrapper
```

### Feedback System Integration

1. Quality Metrics:
```python
def calculate_quality_score(lexical_value):
    metrics = {
        'completeness': check_completeness(lexical_value),
        'accuracy': verify_references(lexical_value),
        'consistency': check_consistency(lexical_value)
    }
    return sum(metrics.values()) / len(metrics)
```

2. Feedback Collection:
```python
def collect_feedback(lexical_value, feedback_data):
    with feedback_lock:
        store_feedback(lexical_value.lemma, feedback_data)
        update_quality_metrics(lexical_value.lemma)
```

### Testing Strategy

1. Parallel Processing Tests:
```python
def test_parallel_generation():
    batch = ["term1", "term2", "term3"]
    results = process_batch(batch)
    assert len(results) == len(batch)
    assert all(r is not None for r in results)
```

2. Performance Benchmarks:
```python
def benchmark_generation(batch_size):
    start = time.time()
    batch = generate_test_batch(batch_size)
    results = process_batch(batch)
    duration = time.time() - start
    return duration / batch_size
```

## Next Actions

1. Implement parallel processing infrastructure
2. Create thread-safe caching mechanism
3. Design feedback collection system
4. Develop quality metrics framework
5. Expand test coverage
6. Update documentation
7. Monitor performance metrics
8. Plan for chatbot interface development

This context provides a foundation for implementing parallel processing and enhancing the feedback system while maintaining the stability of the debugged web interface.
