# Ancient Medical Texts Analysis App

## Project Overview
The Ancient Medical Texts Analysis App is a sophisticated tool designed for analyzing and querying ancient medical texts. It provides a comprehensive pipeline for processing, storing, and retrieving information from a corpus of historical medical documents, with a focus on ancient Greek texts.

## Features
- Corpus management system for efficient handling of ancient texts
- Natural Language Processing (NLP) pipeline for ancient Greek text analysis
- Integration with Large Language Models (LLMs) for advanced text processing and querying
- TLG (Thesaurus Linguae Graecae) parsing and reference processing
- Flexible LLM integration (AWS Bedrock, OpenAI, Anthropic, OpenRouter)
- Custom annotation system for linguistic and semantic tagging
- Search functionality across multiple texts in the corpus
- Lexical value generation and management system
- Command-line interface for interacting with lexical values
- Caching mechanism for improved performance and reduced API calls
- Batch processing for efficient generation of multiple lexical values
- Interactive playground for testing LLMAssistant and LexicalValueGenerator

## Directory Structure
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
│   └── techStack.md
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
│   └── data_parsing/
│       ├── text_parsing.py
│       ├── tlg_parser.py
│       ├── galenus/
│       │   ├── galenus_parsing.py
│       │   └── Untitled-1.ipynb
│       └── hipocrates_sacred_disease/
│           └── hippocrates_parsing.py
└── tests/
    ├── test_lexical_value.py
    └── test_lexical_value_generator.py
```

## Corpus Management System
The Corpus Management System is a central component of the application, providing a unified interface for managing the corpus of ancient medical texts. Key features include:

- Importing and processing raw text files (TLG and non-TLG formats)
- Storing processed texts in an annotated JSONL format
- Retrieving and updating existing texts in the corpus
- Searching across multiple texts using regular expressions
- Robust error handling and logging for improved reliability

## Lexical Value Generation
The Lexical Value Generation system is a core component of the application, responsible for creating comprehensive lexical entries for medical terms found in ancient Greek texts. Key features include:

- Advanced prompt structure for accurate and context-rich lexical value generation
- Batch processing capability for efficient generation of multiple lexical values
- Integration with the Corpus Management System for accessing text data
- Caching mechanism to improve performance and reduce API calls
- Suggestion system for updating existing lexical values with new information

### Prompt Structure
The prompt structure for lexical value generation has been optimized to provide comprehensive and accurate results. It includes:

- Context about ancient Greek medical terminology and philology
- Instructions for generating detailed lexical entries, including lemma, translation, short and long descriptions, related terms, and references
- Guidance on considering different types of medical terms (anatomical, disease names, therapeutic concepts, physiological processes)
- Emphasis on historical context, usage in Hippocratic and Galenic medicine, and evolution of terms over time

Benefits of the new prompt structure:
- More accurate and nuanced lexical entries
- Improved consistency across generated entries
- Better integration of historical context and medical theory
- Enhanced relevance to the field of ancient Greek medicine

### Batch Processing
The new batch processing functionality allows for efficient generation of multiple lexical values at once. This feature:

- Processes multiple texts in a single API call, reducing overall processing time
- Maintains context across related texts, potentially improving the quality of generated lexical values
- Allows for easy scaling of lexical value generation for large corpora

To use batch processing:

```python
generator = LexicalValueGenerator(corpus_manager)
text_ids = ["text_id_1", "text_id_2", "text_id_3"]
lexical_values = generator.generate_lexical_values_batch(text_ids, batch_size=3)
```

## Caching Mechanism
The application implements a caching mechanism to improve performance and reduce API calls to external services like AWS Bedrock. The caching system has the following features:

- Configurable cache size and expiration time
- Automatic cache management (least recently used items are removed when the cache is full)
- Cache statistics for monitoring cache usage

To configure the caching mechanism, you can adjust the following parameters when initializing the LexicalValueGenerator:

```python
generator = LexicalValueGenerator(
    corpus_manager,
    cache_size=100,  # Maximum number of items in the cache
    cache_expiration=3600  # Cache expiration time in seconds
)
```

You can also interact with the cache using the following methods:

- `clear_cache()`: Clears all items from the cache
- `get_cache_stats()`: Returns statistics about the current cache usage

Example usage:
```python
# Clear the cache
generator.clear_cache()

# Get cache statistics
stats = generator.get_cache_stats()
print(f"Current cache size: {stats['size']}")
print(f"Maximum cache size: {stats['max_size']}")
```

## Installation
(Add installation instructions here, including required dependencies and environment setup)

## Usage

### Corpus Management
(Add usage instructions for corpus management here)

### Lexical Value CLI

The Lexical Value CLI provides a command-line interface for interacting with the lexical values in the system. Here are the available commands:

1. List all lexical values:
   ```
   python src/lexical_value_cli.py list
   ```
   This command displays a list of all available lemmas along with their short descriptions.

2. View a specific lexical value:
   ```
   python src/lexical_value_cli.py view --lemma <lemma>
   ```
   This command shows detailed information about a specific lexical value, including any suggested updates if available.

3. Edit a lexical value:
   ```
   python src/lexical_value_cli.py edit --lemma <lemma> --fields <field1,field2,...> --values <value1,value2,...>
   ```
   This command allows you to edit multiple fields of a lexical value at once. The number of fields and values should match.

4. Suggest updates for a lexical value:
   ```
   python src/lexical_value_cli.py suggest --lemma <lemma> --new-text <new_text>
   ```
   This command generates suggested updates for a lexical value based on new information provided.

5. View version history of a lexical value:
   ```
   python src/lexical_value_cli.py history --lemma <lemma>
   ```
   This command displays the version history of a lexical value, showing how it has changed over time.

Replace `<lemma>`, `<field1,field2,...>`, `<value1,value2,...>`, and `<new_text>` with appropriate values.

Example usage:
```
# List all lexical values
python src/lexical_value_cli.py list

# View the lexical value for 'ἀρτηρία'
python src/lexical_value_cli.py view --lemma ἀρτηρία

# Edit multiple fields of 'ἀρτηρία'
python src/lexical_value_cli.py edit --lemma ἀρτηρία --fields translation,short_description --values "artery, windpipe","A blood vessel or the windpipe"

# Suggest updates for 'ἀρτηρία' based on new text
python src/lexical_value_cli.py suggest --lemma ἀρτηρία --new-text "New information about ἀρτηρία in Galen's works..."

# View version history of 'ἀρτηρία'
python src/lexical_value_cli.py history --lemma ἀρτηρία
```

### Interactive Playground

The `playground.py` script provides an interactive environment for testing both the LLMAssistant and LexicalValueGenerator components of the system. This feature allows users to experiment with different queries and lexical value generations in real-time.

To use the interactive playground:

1. Run the playground script:
   ```
   python src/playground.py
   ```

2. Choose the mode you want to use:
   - Enter '1' for LLMAssistant mode
   - Enter '2' for LexicalValueGenerator mode
   - Enter 'escape' to exit the playground

3. In LLMAssistant mode:
   - Enter your question when prompted
   - The system will process your query and return the results

4. In LexicalValueGenerator mode:
   - Enter a word to generate a lexical entry for
   - The system will create and display the lexical entry for the given word

5. The playground will continue to prompt for input until you choose to exit

This interactive environment is particularly useful for:
- Testing the responsiveness and accuracy of the LLMAssistant
- Verifying the quality of generated lexical entries
- Exploring the capabilities of the system in a hands-on manner

Example usage:
```
$ python src/playground.py
Choose mode (1: LLMAssistant, 2: LexicalValueGenerator, 'escape' to exit): 1
Ask me a question: What is the role of ἀρτηρία in ancient Greek medicine?
[System processes the question and displays the answer]

Choose mode (1: LLMAssistant, 2: LexicalValueGenerator, 'escape' to exit): 2
Enter a word to generate a lexical entry for: ἀρτηρία
[System generates and displays the lexical entry for ἀρτηρία]

Choose mode (1: LLMAssistant, 2: LexicalValueGenerator, 'escape' to exit): escape
```

## Contributing
(Add contribution guidelines here)

## License
This project is licensed under the [LICENSE NAME] - see the [LICENSE](LICENSE) file for details.
