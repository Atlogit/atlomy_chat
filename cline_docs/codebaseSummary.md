# Codebase Summary

This document provides an overview of the project structure and key components of the Ancient Medical Texts Analysis App.

## Key Components and Their Interactions

1. Corpus Manager (corpus_manager.py)
   - Main interface for managing the corpus of ancient medical texts
   - Handles importing, processing, and retrieving texts
   - Interacts with TLG Parser and Text Parsing components
   - Manages storage of processed texts in JSONL format

2. LLM Assistant (playground.py)
   - Main interface for querying the processed text data
   - Uses AWS Bedrock for LLM integration
   - Interacts with TLGParser for reference processing
   - Implements a query system that generates Python code to answer user questions about the library of texts

3. TLG Parser (tlg_parser.py)
   - Processes TLG references in texts
   - Loads and uses TLG indexes for author and work information
   - Replaces TLG references with human-readable citations
   - Converts TLG files into annotated JSONL format
   - Uses relative imports for better module organization

4. Text Parsing (text_parsing.py)
   - Uses spaCy for NLP tasks on ancient Greek texts
   - Processes raw text files into annotated JSONL format
   - Implements sentence splitting, text cleaning, and token-level annotation

5. Specialized Parsing Scripts
   - Galenus parsing (galenus_parsing.py)
   - Hippocrates parsing (hippocrates_parsing.py)

6. Lexical Value Generation (lexical_value_generator.py)
   - Generates comprehensive lexical entries for medical terms found in ancient Greek texts
   - Uses an optimized prompt structure for accurate and context-rich generation
   - Implements batch processing for efficient generation of multiple lexical values
   - Integrates with Corpus Manager and reference systems
   - Provides structured lexical entries for important medical terms and concepts
   - Supports versioning and suggestion of updates based on new information
   - Implements a caching mechanism to reduce API calls and improve performance
   - Configurable cache size and expiration time for optimized resource usage

7. Lexical Value Storage (lexical_value_storage.py)
   - Manages the storage and retrieval of lexical values
   - Supports CRUD operations for lexical entries

8. Lexical Value CLI (lexical_value_cli.py)
   - Provides a command-line interface for interacting with lexical values
   - Supports listing, viewing, editing, and suggesting updates for lexical entries
   - Allows viewing version history of lexical values

9. Logging System (logging_config.py)
   - Implements a centralized logging system for the entire application
   - Supports both console and file output
   - Configurable log levels, formats, and output destinations
   - Provides JSON logging option for easier log parsing and analysis
   - Includes functions for dynamically changing log levels at runtime

## Data Flow

1. Raw TLG files / Raw text files → Corpus Manager → TLG Parser / Text Parsing → Annotated JSONL files
2. Annotated JSONL files → Corpus Manager → LLM Assistant for querying
3. User queries → LLM Assistant → Corpus Manager → Processed results
4. Annotated JSONL files → Lexical Value Generation → Structured lexical entries and analyses
5. User input → Lexical Value CLI → Lexical Value Generator / Storage → Updated lexical entries
6. Application-wide → Logging System → Console/File outputs

## External Dependencies

- spaCy and spaCy-transformers: For NLP tasks
- Custom spaCy models:
  - "models/atlomy_full_pipeline_annotation_131024/model-best"
  - "models/model-best"
  - "grc_proiel_trf" (used in tlg_parser.py)
- AWS Bedrock: For LLM integration (ChatBedrock)
- LangChain: For building LLM-powered applications
- Python's built-in logging module: For centralized logging system

## Recent Significant Changes

- Implementation of Corpus Manager for centralized text management
- Integration of flexible LLM choices (AWS Bedrock, OpenAI, Anthropic, OpenRouter)
- Implementation of TLG parsing and reference processing
- Creation of a custom NLP pipeline for ancient Greek text analysis
- Addition of specialized parsing scripts for specific ancient medical texts
- Implementation of Lexical Value Generation system
- Creation of Lexical Value Storage system
- Development of Lexical Value CLI for user interaction
- Implementation of a caching mechanism in the Lexical Value Generator to improve performance and reduce API calls
- Optimization of prompt structure for more accurate and context-rich lexical value generation
- Implementation of batch processing for efficient generation of multiple lexical values
- Update of unit tests to cover new functionality and optimized prompt structure
- Implementation of a centralized logging system with configurable options
- Addition of JSON logging capability for improved log analysis
- Integration of logging across all major components of the application
- Fixed import issues in TLG Parser (tlg_parser.py) by using relative imports for better module organization
- Finalized and optimized the lexical value generation system
- Enhanced integration between LexicalValueGenerator and other components

## Upcoming Developments

- Implementation of advanced caching mechanisms for frequently accessed lexical values
- Exploration of parallel processing for handling multiple lexical value generations
- Development of a feedback mechanism to improve generated lexical values over time
- Expansion of unit test coverage for LexicalValueGenerator and related components
- Creation of a comprehensive user guide for the LexicalValueGenerator
- Planning and design for the chatbot interface
- Research and planning for the implementation of a fact-based response system

## Recent Updates to Logging Configuration

The logging system has been further enhanced with the following updates:

1. Environment Variable Configuration: The logging configuration now uses environment variables to determine log levels, formats, and output destinations. This allows for easier configuration changes without modifying the code.

2. Flexible Output Options: Users can now configure whether logs should be output to the console, file, or both using environment variables.

3. JSON Logging Option: A new option for JSON-formatted logs has been added, which can be enabled via an environment variable. This feature facilitates easier log parsing and analysis, especially in production environments.

4. Dynamic Log Level Changes: A new function `change_log_level()` has been added to allow dynamic changes to the log level at runtime. This is particularly useful for debugging purposes.

5. Consistent Usage Across Components: All major components of the application have been updated to use the centralized logger instance, ensuring consistent logging practices throughout the codebase.

These updates improve the flexibility and maintainability of the logging system, allowing for better debugging and monitoring of the application in various environments.

## Example Files and Data Structures

1. annotation_categories.txt
   - Contains a list of categories used for text annotation, including Body Part, Adjectives/Qualities, Topography, etc.

2. jsonl_example.jsonl
   - Demonstrates the structure of annotated text data
   - Each line is a JSON object representing a sentence or text fragment
   - Contains detailed token-level information including lemma, POS, morphology, and custom categories

3. lexical_entry_examples.json
   - Provides examples of lexical entries for medical terms
   - Each entry includes lemma, translation, short description, and long description
   - Offers detailed etymological and historical information for each term

4. LOGGING.md
   - Documentation on the centralized logging system implemented in the project

5. atlomy_chat.log
   - Contains application-wide logs with configurable level of detail
   - Supports both standard and JSON log formats

These example files showcase the depth and complexity of the data being processed and analyzed by the application. They highlight the need for sophisticated NLP techniques and domain-specific knowledge in ancient Greek medical terminology.

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
├── src/
│   ├── corpus_manager.py
│   ├── index_utils.py
│   ├── playground.py
│   ├── test_corpus_manager.py
│   ├── tlg_index.py
│   ├── lexical_value.py
│   ├── lexical_value_generator.py
│   ├── lexical_value_storage.py
│   ├── lexical_value_cli.py
│   ├── logging_config.py
│   └── data_parsing/
│       ├── text_parsing.py
│       ├── tlg_parser.py
│       ├── galenus/
│       │   ├── galenus_parsing.py
│       │   └── Untitled-1.ipynb
│       └── hipocrates_sacred_disease/
│           └── hippocrates_parsing.py
├── tests/
│   ├── test_lexical_value.py
│   └── test_lexical_value_generator.py
```

This structure reflects the current state of the project, with core functionality in the src directory, documentation in the cline_docs directory, and test files in the tests directory. The logs directory now includes the centralized log file.

## Additional Notes

1. The project includes multiple spaCy models, which may be used for different aspects of text processing or represent different versions of the model.
2. There are specialized parsing scripts for specific ancient medical texts (Galenus and Hippocrates), indicating a focus on these particular authors.
3. The presence of Jupyter notebooks (Untitled-1.ipynb) suggests that some exploratory data analysis or development is being done interactively.
4. The project uses version control (presence of .gitignore file) and has a license file, indicating it's being managed as a formal software project.
5. The cline_docs directory contains important project documentation, including requirements and the tech stack overview.
6. The corpus_manager.py provides a centralized interface for managing the corpus of ancient medical texts, improving the overall organization and efficiency of text processing.
7. The logs directory now includes the centralized log file `atlomy_chat.log`.
8. The lexical value generation system enhances the project's capabilities in summarizing and analyzing key concepts from the ancient medical texts.
9. The Lexical Value CLI provides an easy-to-use interface for researchers and scholars to interact with the lexical entries, supporting manual updates and version tracking.
10. The caching mechanism in the Lexical Value Generator improves performance by reducing API calls to external services, with configurable cache size and expiration time.
11. The optimized prompt structure for lexical value generation ensures more accurate and context-rich entries, considering the nuances of ancient Greek medical terminology.
12. Batch processing functionality allows for efficient generation of multiple lexical values, improving overall system performance when dealing with large corpora.
13. The centralized logging system enhances debugging capabilities and provides consistent logging across all components of the application.
14. The new logging system supports both standard and JSON log formats, allowing for easier integration with log analysis tools.
15. Log levels can be dynamically changed at runtime, providing flexibility in adjusting the verbosity of logs as needed during development or production.
16. The TLG Parser now uses relative imports, improving module organization and reducing potential import issues.

This comprehensive structure allows for specialized processing of different ancient medical texts while maintaining a flexible and extensible architecture for future developments. The recent optimizations and additions to the Lexical Value Generation system and the new centralized logging system further enhance the project's functionality, accuracy, performance, and maintainability. The upcoming developments will focus on further performance improvements, user interaction, and preparing for the next phase of the project.

## Logging Configuration

The logging configuration is set up in `src/logging_config.py` using environment variables. It supports both console and file output with configurable log levels, formats, and JSON logging for easier analysis. The logger instance is used across all components to ensure consistent logging throughout the application.
