# Codebase Summary

This document provides an overview of the project structure and key components of the Ancient Medical Texts Analysis App.

## Key Components and Their Interactions

1. Web Interface (`static/`)
   - Frontend for user interactions with the system
   - Three main sections matching core functionality
   - Components:
     - `index.html`: Main interface structure with proper static file references
     - `styles.css`: Modern, responsive styling
     - `app.js`: Client-side logic and API integration
   - Features:
     - Interactive query interface
     - CRUD operations for lexical values
     - Corpus management tools
     - Real-time API communication

2. Backend API (`app/api.py`)
   - FastAPI application serving the web interface
   - RESTful endpoints for all core functionality
   - Integrates with LLMAssistant, LexicalValueGenerator, and CorpusManager
   - Proper error handling and logging
   - Static file serving configuration
   - Endpoint categories:
     - LLM queries
     - Lexical value operations
     - Corpus management

3. Corpus Manager (`src/corpus_manager.py`)
   - Main interface for managing the corpus of ancient medical texts
   - Handles importing, processing, and retrieving texts
   - Interacts with TLG Parser and Text Parsing components
   - Manages storage of processed texts in JSONL format
   - Implements search functionality with lemma support
   - Initialized with correct corpus directory path

4. LLM Assistant (`src/playground.py`)
   - Main interface for querying the processed text data
   - Uses AWS Bedrock for LLM integration (Claude-3-sonnet)
   - Interacts with TLGParser for reference processing
   - Implements a query system that generates Python code to answer user questions
   - Supports interactive testing and development
   - Configured for optimal response generation

5. TLG Parser (`src/tlg_parser.py`)
   - Processes TLG references in texts
   - Loads and uses TLG indexes for author and work information
   - Replaces TLG references with human-readable citations
   - Converts TLG files into annotated JSONL format
   - Uses relative imports for better module organization
   - Properly initialized with citation configuration

6. Text Parsing (`src/text_parsing.py`)
   - Uses spaCy for NLP tasks on ancient Greek texts
   - Processes raw text files into annotated JSONL format
   - Implements sentence splitting, text cleaning, and token-level annotation
   - Integrated with corpus management system

7. Specialized Parsing Scripts
   - Galenus parsing (`src/data_parsing/galenus/galenus_parsing.py`)
   - Hippocrates parsing (`src/data_parsing/hipocrates_sacred_disease/hippocrates_parsing.py`)

8. Lexical Value Generation (`src/lexical_value_generator.py`)
   - Generates comprehensive lexical entries for medical terms
   - Uses Claude-3-haiku for efficient and accurate generation
   - Implements caching for improved performance
   - Supports batch processing and version history
   - Integrates with Corpus Manager and reference systems
   - Provides structured lexical entries with rich metadata
   - Implements error handling and comprehensive logging
   - Configurable cache size and expiration time

9. Lexical Value Storage (`src/lexical_value_storage.py`)
   - Manages persistent storage of lexical values
   - Implements version history tracking
   - Supports CRUD operations for lexical entries
   - Handles file-based storage with JSON format
   - Implements caching for frequently accessed values
   - Provides backup and recovery mechanisms
   - Ensures data consistency and integrity

10. Server Configuration (`app/run_server.py`)
    - Configures and runs the FastAPI development server
    - Uses uvicorn ASGI server
    - Supports hot reloading for development
    - Configurable host and port settings
    - Proper Python path configuration

## Data Flow

1. Web Interface Flow:
   - User interacts with frontend components
   - Frontend makes API calls to backend endpoints
   - Backend processes requests through core components
   - Results are returned and displayed in the UI

2. Text Processing Flow:
   - Raw text files → TLG Parser → Annotated JSONL files
   - Annotated JSONL files → Corpus Manager → LLM Assistant for querying
   - User queries → LLM Assistant → Corpus Manager → Processed results

3. Lexical Value Flow:
   - User input → Lexical Value CLI/Web Interface → Lexical Value Generator/Storage
   - Lexical value requests → Cache check → LLM generation if needed → Storage
   - Updates and deletions → Storage → Version history tracking

4. Application-wide Logging:
   - All components → Logging System → Console/File outputs
   - Centralized configuration
   - Comprehensive error tracking

## Project Structure

```
/root/Projects/Atlomy/git/atlomy_chat/
├── .gitignore
├── atlomy_chat.code-workspace
├── LICENSE
├── README.md
├── assets/
├── cline_docs/
│   ├── codebaseSummary.md
│   ├── currentTask.md
│   ├── projectRoadmap.md
│   ├── requirements.md
│   ├── techStack.md
│   └── LOGGING.md
├── logs/
│   └── atlomy_chat.log
├── static/
│   ├── index.html
│   ├── styles.css
│   └── app.js
├── app/
│   ├── __init__.py
│   ├── api.py
│   └── run_server.py
├── src/
│   ├── corpus_manager.py
│   ├── index_utils.py
│   ├── playground.py
│   ├── lexical_value.py
│   ├── lexical_value_generator.py
│   ├── lexical_value_storage.py
│   ├── lexical_value_cli.py
│   ├── logging_config.py
│   └── data_parsing/
│       ├── text_parsing.py
│       ├── tlg_parser.py
│       ├── galenus/
│       │   └── galenus_parsing.py
│       └── hipocrates_sacred_disease/
│           └── hippocrates_parsing.py
├── tests/
│   ├── test_lexical_value.py
│   └── test_lexical_value_generator.py
```

## Additional Notes

1. The project uses multiple spaCy models for different aspects of text processing
2. Specialized parsing scripts exist for specific ancient medical texts
3. The project maintains comprehensive documentation in the cline_docs directory
4. The logging system provides flexible configuration through environment variables
5. The lexical value generation system includes caching and version history
6. Both CLI and web interfaces provide user-friendly access to system functionality
7. Test coverage is being continuously expanded
8. Performance optimizations are being implemented across the system
9. Documentation is regularly updated to reflect system changes
10. The project follows best practices for code organization and modularity
11. Error handling and logging are implemented consistently across components
12. The system is designed for extensibility and future enhancements
13. Caching mechanisms improve performance for frequently accessed data
14. Version history tracking maintains data integrity and allows for rollbacks
15. The web interface provides modern, responsive access to all core functionality

This comprehensive structure allows for specialized processing of different ancient medical texts while maintaining a flexible and extensible architecture for future developments. The web interface and API layer provide easy access to all functionality, with proper error handling and logging throughout the system.
