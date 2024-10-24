# Requirements Document for Ancient Medical Texts Analysis App

## 1. Corpus Management System (Implemented)
- Ability to import and manage various ancient medical texts
- Support for TLG (Thesaurus Linguae Graecae) formatted files
- Conversion of raw text files into annotated JSONL format
- Storage and retrieval of processed texts

## 2. Natural Language Processing Pipeline (Initial Implementation Complete)
- Integration with spaCy and custom models for ancient Greek text analysis
- Sentence splitting and tokenization
- Part-of-speech tagging and lemmatization
- Morphological analysis
- Named entity recognition for medical terms and concepts
- Custom category annotation based on predefined categories (e.g., Body Part, Adjectives/Qualities, Topography)

## 3. Reference Gathering and Citation System (Partially Implemented)
- Parsing and processing of TLG references
- Conversion of TLG references into human-readable citations
- Integration with TLG indexes for author and work information

## 4. Lexical Value Generation (Current Focus)
- Creation and management of lexical entries for medical terms
- Support for multiple fields in lexical entries: lemma, translation, short description, long description
- Ability to generate summaries and academic analyses based on the processed texts
- Integration with the existing NLP pipeline for efficient term extraction and analysis
- Versioning system for tracking changes and updates to lexical entries
- Caching mechanism for improved performance in lexical value retrieval

## 5. Web Interface (Implemented)
- Modern, responsive frontend design using Tailwind CSS and DaisyUI
- Node.js >= 20.18.0 for development tooling
- Three main functional sections:
  - LLM Assistant interface with card-based layout
  - Lexical Value management with enhanced form controls
  - Corpus Manager access with modern UI components
- Frontend Dependencies:
  - Tailwind CSS (v3.4.1) for utility-first styling
  - DaisyUI (v4.7.2) for pre-built components
  - PostCSS (v8.4.35) for CSS processing
  - Autoprefixer (v10.4.17) for browser compatibility
- Frontend Build System:
  - NPM scripts for CSS compilation
  - Watch mode for development
  - Optimized production builds
- FastAPI backend with RESTful endpoints
- Static file serving
- Error handling and user feedback
- Real-time result display
- Clean, intuitive user experience with modern components:
  - Card layouts
  - Tabbed navigation
  - Form controls
  - Code blocks
  - Buttons and inputs
- Cross-browser compatibility
- Mobile-responsive design
- Themeable interface using DaisyUI themes

## 6. Fact-based Response System (Planned)
- Generation of Python code to answer user queries about the text library
- Execution of generated code to retrieve relevant information
- Presentation of results with proper citations and references

## 7. LLM Integration (Planned)
- Flexible integration with multiple LLM providers (AWS Bedrock, OpenAI, Anthropic, OpenRouter)
- Ability to switch between different LLM models for various tasks

## 8. Data Structures and File Formats (Implemented)
- Support for JSONL format for annotated text data
- JSON format for lexical entries
- Plain text format for annotation categories and other configuration files

## 9. Specialized Text Processing (Partially Implemented)
- Custom parsing scripts for specific ancient medical texts (e.g., Galen, Hippocrates)
- Ability to handle unique formatting and citation styles of different authors

## 10. Performance and Scalability
- Efficient processing of large volumes of ancient texts
- Optimization for quick response times in the chatbot interface
- Scalable architecture to accommodate growing text corpora and user base

## 11. User Management and Access Control (Planned)
- User authentication and authorization system
- Role-based access control for different features (e.g., corpus management, querying)

## 12. Logging and Monitoring (Implemented)
- Comprehensive logging of system activities and user interactions
- Monitoring of system performance and resource usage

## 13. Data Export and Interoperability (Planned)
- Ability to export processed texts and lexical entries in standard formats
- API for integration with other research tools and platforms

## 14. Customization and Extensibility
- Configurable annotation categories and processing rules
- Plugin system for adding new features or integrating with additional tools

## 15. Documentation and Help System (Ongoing)
- Comprehensive user manual and API documentation
- In-app help system and tooltips for user guidance

## 16. Testing and Quality Assurance (Ongoing)
- Automated testing suite for NLP pipeline, data processing, and query system
- Validation tools for ensuring accuracy of annotations and lexical entries

## 17. Deployment and Maintenance (Planned)
- Easy deployment process for different environments (development, staging, production)
- Regular update mechanism for LLM models, NLP components, and application features

## 19. Development Environment Requirements (Updated)
- Conda environment:
  - Name: atlomy_chat
  - Python version: 3.11 or later
- Node.js >= 20.18.0 (LTS) installed within the conda environment
- NPM >= 10.8.2
- Development Dependencies:
  - tailwindcss: ^3.4.1
  - daisyui: ^4.7.2
  - postcss: ^8.4.35
  - autoprefixer: ^10.4.17
  - jest: ^29.7.0
  - @testing-library/react: ^16.0.1
  - @testing-library/jest-dom: ^6.6.2
  - @types/jest: ^29.5.14
  - jest-environment-jsdom: ^29.7.0
- Build System Requirements:
  - CSS processing pipeline
  - Watch mode for development
  - Production optimization
  - Minification for production builds
- Version Control:
  - package.json for dependency management
  - Configuration files for build tools:
    - tailwind.config.js for Tailwind and DaisyUI configuration
    - postcss.config.js for PostCSS plugins
    - jest.config.js for Jest configuration
    - jest.setup.js for Jest setup
  - CSS source maps for development
- Environment Setup:
  - setup_conda_env.sh script for creating and configuring the conda environment
  - Activation of conda environment required before running the application or tests

These requirements reflect the current state of the Ancient Medical Texts Analysis App, including the upgraded UI framework with the latest versions of Tailwind CSS and DaisyUI components, as well as the new testing setup with Jest and React Testing Library. The development environment now requires the use of a conda environment for better isolation and reproducibility. The current focus remains on performance optimization through parallel processing, enhanced feedback mechanisms, and comprehensive testing, while maintaining and improving the existing functionality with modern UI components.

These requirements reflect the current state of the Ancient Medical Texts Analysis App, including the upgraded UI framework with the latest versions of Tailwind CSS and DaisyUI components. The current focus remains on performance optimization through parallel processing and enhanced feedback mechanisms, while maintaining and improving the existing functionality with modern UI components.
