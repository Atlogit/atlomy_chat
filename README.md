# Ancient Medical Texts Analysis App

## Project Overview
The Ancient Medical Texts Analysis App is a sophisticated tool designed for analyzing and querying ancient medical texts. It provides a comprehensive pipeline for processing, storing, and retrieving information from a corpus of historical medical documents, with a focus on ancient Greek texts. The application now features a modern web interface built with Next.js, enhancing user interaction and accessibility.

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
- Modern web interface built with Next.js for improved user experience
- Comprehensive testing suite using Jest and React Testing Library

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
├── tests/
│   ├── test_lexical_value.py
│   └── test_lexical_value_generator.py
└── next-app/
    ├── src/
    │   ├── app/
    │   ├── components/
    │   │   ├── layout/
    │   │   ├── sections/
    │   │   └── ui/
    │   ├── hooks/
    │   └── utils/
    ├── public/
    ├── jest.config.js
    ├── jest.setup.js
    └── package.json
```

## Next.js Migration
The application has been successfully migrated to use Next.js, a React framework that enables server-side rendering and generates static websites for React-based web applications. This migration brings several benefits:

- Improved performance through server-side rendering and static site generation
- Enhanced SEO capabilities
- Simplified routing and API routes
- Better developer experience with hot module replacement and error reporting

The new web interface is located in the `next-app/` directory and includes components for different sections of the application (LLM, Lexical, and Corpus management).

## Testing Infrastructure
A comprehensive testing suite has been implemented using Jest and React Testing Library. The tests cover:

- UI components (Button, ResultsDisplay, ProgressDisplay)
- Layout components (Header, Navigation)
- Section components (LLMSection, LexicalSection, CorpusSection)
- API integration
- Form submissions
- Batch operations
- Progress tracking
- Error handling

All planned testing tasks have been completed, providing a robust foundation for maintaining and expanding the application.

## Documentation
The project now includes comprehensive documentation to aid developers in understanding and contributing to the codebase:

1. Main README.md (this file): Provides an overview of the entire project, including setup instructions and usage guidelines.
2. Component Documentation (`next-app/src/components/README.md`): Describes the structure and purpose of React components used in the frontend.
3. Hooks Documentation (`next-app/src/hooks/README.md`): Explains custom React hooks and their usage.
4. Utils Documentation (`next-app/src/utils/README.md`): Details utility functions and modules used across the application.
5. Codebase Summary (`cline_docs/codebaseSummary.md`): Offers a high-level overview of the project structure and key components.

## Current Focus
The project is currently focused on the following areas:

1. Completing comprehensive documentation
   - Adding JSDoc comments to components
   - Updating API documentation
   - Creating a component usage guide
   - Documenting state management patterns
   - Adding detailed setup instructions
2. Optimizing performance
3. Enhancing accessibility
4. Preparing for production deployment

## Usage

### Setting Up the Environment

1. Activate the conda environment:
   ```
   source /root/miniconda3/bin/activate atlomy_chat
   ```
   or
   '''
   conda activate atlomy_chat
   '''

2. Ensure you have the correct Node.js and npm versions:
   - Required Node.js version: v20.18.0
   - Required npm version: 10.8.2

   To check your current versions:
   ```
   node --version
   npm --version
   ```

   If you need to update Node.js, you can use nvm (Node Version Manager):
   ```
   source ~/.nvm/nvm.sh
   nvm install 20.18.0
   nvm use 20.18.0
   ```

   npm should be automatically updated with Node.js, but if not, you can update it manually:
   ```
   npm install -g npm@10.8.2
   ```

### Running the Web Application

1. Start the FastAPI backend:
   ```
   python app/run_server.py
   ```

2. Navigate to the `next-app/` directory:
   ```
   cd next-app
   ```

3. Install dependencies:
   ```
   npm install
   ```

4. Start the development server:
   ```
   npm run dev
   ```

5. Open your browser and visit `http://localhost:3000` to access the application.

### Running the Application in Debug Mode

To run the application in debug mode for backend debugging:

1. Ensure you are in the project root directory.

2. Run the debug script:
   ```
   bash run_debug.sh
   ```

This will start the backend server in debug mode, allowing you to set breakpoints and debug the backend code.

### Running Tests

To run tests, use the following commands in the `next-app` directory:

- Run all tests: `npm test`
- Run tests in watch mode: `npm run test:watch`
- Generate test coverage report: `npm run test:coverage`


## Contributing
(Add contribution guidelines here)

## License
This project is licensed under the [LICENSE NAME] - see the [LICENSE](LICENSE) file for details.
