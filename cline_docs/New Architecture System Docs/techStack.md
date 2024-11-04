# Tech Stack

This document outlines the key technologies, frameworks, and tools used in the Ancient Medical Texts Analysis App.

## Core Technologies

### Programming Languages
- Python 3.9+: Primary language for backend development and NLP tasks
- TypeScript 5.6.3: Frontend development with type safety
- HTML/CSS: Frontend structure and styling with Tailwind CSS

### Backend Framework
- FastAPI: Modern, high-performance web framework
  - RESTful API endpoints
  - Static file serving
  - Automatic OpenAPI documentation
  - Built-in error handling
  - SSE (Server-Sent Events) support via sse-starlette
- Uvicorn: ASGI server implementation

### Database & Storage
- PostgreSQL with asyncpg driver
  - JSONB for flexible data storage
  - Async database operations
- SQLAlchemy: ORM and database toolkit
- Alembic: Database migrations
- Redis (aioredis >= 2.0.0): Caching layer
- AWS S3 (boto3): Cloud storage

### Data Processing
- Pandas: Data manipulation and analysis
- NumPy: Numerical computing
- Pydantic: Data validation
- Typing extensions: Enhanced type hints

### Frontend
- Next.js 15.0.1: React framework
  - Server-side rendering
  - API routes
  - File-based routing
  - Built-in optimization
- React 18.3.1: UI library
- TypeScript: Static typing
- TailwindCSS 3.4.14: Utility-first CSS framework
  - Just-In-Time engine
  - Built-in PurgeCSS
  - Modern browser support
  - Custom plugin support
- DaisyUI 4.12.13: Component library
  - Pre-built UI components
  - Theme system
  - Responsive design
  - Accessibility features

## NLP & Machine Learning

### Core NLP Stack
- spaCy with CUDA 12.x support
  - Transformer models
  - Entity recognition
  - Linguistic annotations
- spaCy-transformers: Advanced NLP capabilities
- spaCy-lookups-data: Additional linguistic data

### LLM Integration
- LangChain: LLM framework
- AWS Bedrock integration via langchain-aws
- Custom services:
  - Token management
  - Context handling
  - Streaming support

## Development Tools

### Version Control
- Git: Source code management
- GitPython: Git operations from Python

### Code Quality & Testing
- ESLint 9.13.0: JavaScript/TypeScript linting
- Jest 29.7.0: JavaScript testing
  - jest-environment-jsdom
  - @testing-library/jest-dom
  - @testing-library/react
  - @testing-library/user-event
- Pytest: Python testing
  - pytest-asyncio
  - pytest-cov
  - Coverage reporting
- TypeScript type checking

### Build Tools
- Node.js (>= 20.18.0 LTS): JavaScript runtime
- NPM (>= 10.8.2): Package management
- PostCSS 8.4.47: CSS processing
  - Autoprefixer 10.4.20
  - Plugin ecosystem
- Babel 7.x: JavaScript compiler
  - React JSX support
  - TypeScript support

## Build Process

### Development
1. Frontend development:
   ```bash
   npm run dev  # Next.js development server
   ```
   - Hot module replacement
   - Fast refresh
   - TypeScript compilation

2. CSS processing:
   ```bash
   npm run dev  # Tailwind watch mode
   ```
   - Watches input.css
   - Compiles Tailwind utilities
   - Updates styles.css in real-time

3. Backend development:
   ```bash
   uvicorn app.main:app --reload
   ```
   - Auto-reload
   - Debug mode
   - API documentation

### Production
1. Frontend build:
   ```bash
   npm run build
   ```
   - Production optimization
   - Code splitting
   - Static generation

2. CSS optimization:
   ```bash
   npm run build  # Tailwind production build
   ```
   - Purges unused CSS
   - Minifies output
   - Optimizes for production

## Additional Tools

### HTTP Clients
- HTTPX: Async HTTP client
- Async support via asyncio

### Environment & Configuration
- python-dotenv: Environment variables
- pydantic-settings: Settings management

### Logging & Monitoring
- Loguru: Enhanced logging
- Custom logging configuration
- Performance monitoring

### Documentation
- Automatic API documentation (FastAPI)
- Type hints and docstrings
- Inline code documentation

Note: This tech stack document reflects the current state of the project with all dependencies updated to their latest stable versions as found in package.json, requirements.txt, and various configuration files. The modern tooling ensures optimal development experience, robust testing, efficient API handling, and production performance while maintaining compatibility with current web standards.
