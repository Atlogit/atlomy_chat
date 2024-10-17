# Tech Stack

This document outlines the key technologies, frameworks, and tools used in the Ancient Medical Texts Analysis App.

## Core Technologies

### Programming Languages
- Python: Primary language for backend development and NLP tasks

### Natural Language Processing
- spaCy: For text processing, tokenization, and linguistic feature extraction
- spaCy-transformers: For advanced NLP tasks using transformer models

### Machine Learning
- LangChain: Framework for developing applications with large language models (LLMs)

### Large Language Models
- Flexible LLM integration: The system is designed to work with multiple LLM providers and models for different tasks
  - AWS Bedrock: For accessing various LLMs including Claude and other models
  - OpenAI API: For GPT models
  - Anthropic API: For direct access to Claude models
  - OpenRouter: For accessing multiple LLM providers through a single API
- Potential use of multiple models for different steps in the analysis pipeline

### Data Storage and Processing
- JSONL: Used for storing and processing structured data

## Frameworks and Libraries

### Backend
- LangChain: For building LLM-powered applications
- Potential integration with other LLM frameworks for specific tasks

### Cloud Services
- AWS Bedrock: Primary service for accessing and utilizing various LLMs
- Potential integration with other cloud services for specific LLM access or computational needs

## Development Tools

### Version Control
- Git: For source code management

### Code Editor
- Visual Studio Code: Primary integrated development environment (IDE)

## Data Formats

### Text Corpus
- Custom TLG (Thesaurus Linguae Graecae) format: For storing and processing ancient Greek texts

### Annotations
- Custom annotation format: For storing linguistic and semantic annotations of texts

## Additional Tools

### Data Parsing
- Custom scripts for parsing and processing TLG format texts

### Text Analysis
- Custom NLP pipeline for ancient Greek text analysis

## To Be Determined
- Database system for storing processed data and lexical entries
- Web framework for building the user interface (if required)
- Deployment and hosting solution
- Specific LLM models and providers for each step in the analysis pipeline
- Integration strategy for multiple LLM providers and models

Note: This tech stack document will be updated as the project progresses and more specific technology decisions are made. The flexible approach to LLM integration allows for easy adaptation to new models and providers as they become available or as project needs evolve.
