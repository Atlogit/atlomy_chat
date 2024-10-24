# Project Context: Ancient Medical Texts Analysis App

## Quick Start Guide for LLM-Coder

1. **Current Status**: Web Interface Enhanced and Modernized
   - Updated to latest Node.js (v20.18.0) and npm (10.8.2)
   - Upgraded to latest Tailwind CSS (v3.4.1) and DaisyUI (v4.7.2)
   - Enhanced UI with modern animations and transitions
   - Improved error handling and loading states
   - Responsive design optimized for all devices
   - Comprehensive frontend documentation:
     * See ui_guide.md for HTML/CSS patterns and components
     * See frontend_guide.md for JavaScript patterns and development workflow

2. **Next Steps**:
   a. Implement parallel processing architecture
      - Design thread-safe data structures
      - Create worker pool management
      - Implement load balancing
      - Add performance monitoring
   b. Enhance feedback system
      - Design feedback collection interface (refer to ui_guide.md for component patterns)
      - Create quality metrics framework
      - Implement feedback integration pipeline (refer to frontend_guide.md for API integration)
      - Add automated improvement suggestions
   c. Expand testing framework
      - Add parallel processing tests
      - Create performance benchmarks
      - Implement stress testing
      - Add integration tests (refer to frontend_guide.md for testing practices)

3. **Key Files to Review**:
   - `/app/api.py`: FastAPI application with endpoint definitions
   - `/static/index.html`: Modern UI structure (see ui_guide.md for patterns)
   - `/static/app.js`: Enhanced client-side logic (see frontend_guide.md for patterns)
   - `/static/input.css`: Tailwind CSS and custom styles (see ui_guide.md)
   - `/static/styles.css`: Compiled CSS output
   - `/src/lexical_value_generator.py`: Core generation functionality
   - `/src/lexical_value_storage.py`: Storage and caching system
   - `/src/corpus_manager.py`: Text management and search
   - `/src/logging_config.py`: Centralized logging system
   - `/tests/test_lexical_value_generator.py`: Unit tests
   - `/cline_docs/ui_guide.md`: HTML/CSS patterns and components
   - `/cline_docs/frontend_guide.md`: JavaScript patterns and workflow

4. **Tech Stack Highlights**:
   - Python 3.x with multiprocessing
   - FastAPI for web API
   - AWS Bedrock (Claude-3) for LLM
   - Node.js v20.18.0 for frontend tooling
   - Tailwind CSS v3.4.1 for styling (see ui_guide.md)
   - DaisyUI v4.7.2 for UI components (see ui_guide.md)
   - PostCSS v8.4.35 for CSS processing
   - Modern JavaScript patterns (see frontend_guide.md)
   - spaCy for NLP
   - Custom caching system
   - JSON/JSONL for data storage
   - Comprehensive logging system
   - pytest for testing

5. **Recent Updates**:
   - Upgraded Node.js and npm to latest versions
   - Updated all frontend dependencies
   - Enhanced UI with modern animations (see ui_guide.md)
   - Added loading states and spinners (see frontend_guide.md)
   - Improved error handling (see frontend_guide.md)
   - Optimized responsive design (see ui_guide.md)
   - Added smooth transitions
   - Enhanced button feedback
   - Created comprehensive frontend documentation:
     * ui_guide.md for HTML/CSS patterns
     * frontend_guide.md for JavaScript development

6. **Project Structure**:
   - `/app/`: API and server configuration
   - `/static/`: Frontend files (refer to ui_guide.md and frontend_guide.md)
     - `index.html`: Modern UI structure
     - `app.js`: Enhanced client-side logic
     - `input.css`: Tailwind and custom styles
     - `styles.css`: Compiled CSS
   - `/src/`: Core application code
   - `/tests/`: Test suites
   - `/cline_docs/`: Documentation
     - `ui_guide.md`: HTML/CSS patterns
     - `frontend_guide.md`: JavaScript patterns
     - `requirements.md`: System requirements
     - `techStack.md`: Technology stack
     - `context.md`: Project context
   - `/logs/`: Log files
   - `/data_parsing/`: Text parsers

7. **Key Considerations**:
   - Thread safety in parallel processing
   - Cache consistency across processes
   - Performance monitoring and optimization
   - Error handling in distributed operations (see frontend_guide.md)
   - Data integrity in concurrent operations
   - Test coverage for parallel scenarios
   - Documentation of concurrent patterns
   - Frontend best practices (refer to ui_guide.md and frontend_guide.md)
   - Cross-browser compatibility
   - Mobile responsiveness (see ui_guide.md)

8. **Development Guidelines**:
   - Follow test-driven development
   - Maintain comprehensive documentation
   - Use centralized logging
   - Ensure thread safety
   - Monitor performance metrics
   - Handle errors gracefully (see frontend_guide.md)
   - Keep code modular and extensible
   - Follow modern frontend practices:
     * UI patterns from ui_guide.md
     * JavaScript patterns from frontend_guide.md
   - Optimize for performance
   - Ensure accessibility (see ui_guide.md)

9. **Getting Started**:
   - Server runs on http://localhost:8000
   - API documentation at /docs
   - Static files served from /static
   - Logging configured via environment variables
   - Hot reloading enabled for development
   - Frontend development (see frontend_guide.md):
     ```bash
     npm run dev  # Watch mode for CSS
     npm run build  # Production build
     ```
   - UI Components (see ui_guide.md):
     * Layout patterns
     * Form components
     * Button styles
     * Responsive design

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
3. Design feedback collection system (refer to ui_guide.md)
4. Develop quality metrics framework
5. Expand test coverage (see frontend_guide.md)
6. Monitor performance metrics
7. Plan for chatbot interface development:
   - Follow UI patterns from ui_guide.md
   - Implement using patterns from frontend_guide.md
8. Consider additional UI enhancements:
   - Dark mode support (see ui_guide.md)
   - Advanced animations
   - Real-time updates (see frontend_guide.md)
   - Enhanced error visualization
   - Accessibility improvements

This context reflects the current state of the project with modernized frontend, enhanced user experience, and comprehensive documentation for frontend development. Refer to ui_guide.md and frontend_guide.md for detailed implementation patterns and best practices.
