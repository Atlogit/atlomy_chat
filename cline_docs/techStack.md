# Tech Stack

This document outlines the key technologies, frameworks, and tools used in the Ancient Medical Texts Analysis App.

## Core Technologies

### Programming Languages
- Python: Primary language for backend development and NLP tasks
- JavaScript: Frontend client-side logic
- HTML/CSS: Frontend structure and styling with Tailwind CSS

### Web Framework
- FastAPI: Modern, high-performance web framework
  - RESTful API endpoints
  - Static file serving
  - Automatic OpenAPI documentation
  - Built-in error handling
- Uvicorn: ASGI server implementation

### Frontend
- HTML5: Semantic markup and structure
- CSS3: Modern styling with Tailwind CSS and DaisyUI
  - Utility-first CSS framework (v3.4.1)
  - Component-based design system
  - Responsive design utilities
  - Theme system
  - Content-first purging
  - Modern browser support
- JavaScript (ES6+): Client-side interactivity
  - Fetch API for HTTP requests
  - Async/await for asynchronous operations
  - DOM manipulation
  - Event handling
  - Modern module system

### Frontend Build Tools
- Node.js (>= 20.18.0 LTS): JavaScript runtime for build tools
- NPM (>= 10.8.2): Package management
- Tailwind CSS (v3.4.1): Utility-first CSS framework
  - Just-In-Time engine
  - Built-in PurgeCSS
  - Modern browser support
  - Custom plugin support
  - Advanced configuration options
- DaisyUI (v4.7.2): Component library for Tailwind CSS
  - Pre-built UI components
  - Theme system with light/dark mode
  - Responsive design
  - Accessibility features
  - Modern component variants
- PostCSS (v8.4.35): CSS processing
  - Modern CSS features
  - Plugin ecosystem
  - Performance optimization
- Autoprefixer (v10.4.17): Browser compatibility
  - Automatic vendor prefixing
  - Modern browser support
  - CSS Grid support

## Development Tools

### Version Control
- Git: For source code management
- NPM: For frontend dependency management
  - package.json for dependency tracking
  - package-lock.json for deterministic builds

### Code Editor
- Visual Studio Code: Primary integrated development environment (IDE)
  - Extension support
  - Integrated terminal
  - Git integration
  - Debugging tools

### Build and Development
- NPM Scripts: Frontend build automation
  - Development server with watch mode
  - Production builds with minification
  - CSS processing pipeline
  - Test running and coverage reporting
- Tailwind CSS CLI: CSS compilation
  - Watch mode for development
  - JIT compilation
  - Minification for production
- Configuration Files:
  - tailwind.config.js: Tailwind and DaisyUI settings
  - postcss.config.js: PostCSS plugin configuration
  - jest.config.js: Jest testing configuration
  - .babelrc: Babel configuration for TypeScript and React
  - Package management and scripts

### Testing
- Jest (v29.7.0): JavaScript testing framework
  - Unit testing
  - Integration testing
  - Mocking capabilities
  - Code coverage reporting
- React Testing Library: Testing utilities for React components
  - Component rendering
  - DOM querying
  - User event simulation
- Babel (v7.x): JavaScript compiler
  - TypeScript support
  - React JSX support
  - Modern JavaScript features

## Build Process

### Development
1. Watch mode for CSS changes:
   ```bash
   npm run dev
   ```
   - Watches input.css for changes
   - Compiles Tailwind utilities
   - Processes PostCSS features
   - Updates styles.css in real-time

### Production
1. Optimized build process:
   ```bash
   npm run build
   ```
   - Purges unused CSS
   - Minifies output
   - Optimizes for production
   - Generates sourcemaps

## Additional Tools

### Frontend Development
- Modern build pipeline:
  - CSS processing with PostCSS
  - Utility-first development with Tailwind
  - Component library with DaisyUI
  - Browser compatibility with Autoprefixer
- Development workflow:
  - Hot reload for CSS changes
  - Real-time compilation
  - Error reporting
  - Source maps for debugging
- Production optimization:
  - CSS minification
  - Dead code elimination
  - Modern browser optimizations
  - Performance best practices
  
### Lexical Value Generation
- LexicalValueGenerator: Custom module for generating lexical entries
  - Single lexical value creation process
  - Integration with AWS Bedrock for LLM capabilities
  - Claude-3-sonnet model for efficient and accurate generation
  - Asynchronous task-based creation process
  - Error handling and comprehensive logging
- AWS Bedrock: Managed service for foundation models
  - API integration for LLM capabilities
  - Scalable and efficient model inference
- Corpus Manager: Custom module for managing the corpus of ancient medical texts
  - Text processing and storage
  - Integration with LexicalValueGenerator for context and citations

### API Integration
- Custom `useApi` hook: Reusable API call management
  - Consistent error handling
  - Retry mechanism with exponential backoff
  - Loading state management
  - Caching for frequently accessed data
  - Progress tracking for long-running operations
- Axios: Promise-based HTTP client
  - Request and response interceptors
  - Automatic request and response transformations
  - Client-side protection against XSRF

### Error Handling
- ErrorBoundary component: Graceful error management for React components
- Standardized error reporting: Consistent error messages across the application
- Improved error logging: Enhanced debugging capabilities

### Performance Optimization
- Caching strategies: Implemented in `useApi` hook
- Batch operation optimization: Progress tracking and efficient data processing
- React.memo and useMemo: Selective component and value memoization

### Documentation
- JSDoc: Inline documentation for JavaScript and TypeScript
- Storybook (planned): Interactive component documentation and testing

Note: This tech stack document reflects the current state of the project with all dependencies updated to their latest stable versions. The modern tooling ensures optimal development experience, robust testing, efficient API handling, and production performance while maintaining compatibility with current web standards.
