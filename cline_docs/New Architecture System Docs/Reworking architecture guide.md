Here's a comprehensive guide on the **New Architecture and Migration Strategy** for the Ancient Medical Texts Analysis project. This document is structured to be clear and actionable, covering what we aim to achieve, why we’re making these changes, and a detailed plan for the new architecture, migration, and component separation. 

---

# Ancient Medical Texts Analysis: Database Migration and Architecture Guide

## Project Background and Goals

### Current System Overview
Our current setup for analyzing ancient medical texts in Greek, Arabic, and Latin is as follows:
- **Frontend**: HTML5 with Tailwind CSS and DaisyUI components for a user-friendly interface.
- **Backend**: FastAPI with Python 3.9+ for API management.
- **Text Processing**: We use a combination of custom scripts, regular expressions, and spaCy NLP models to process texts.
- **LLM Integration**: AWS Bedrock (Claude-3-sonnet) provides advanced natural language analysis for term summarization and additional insights.
- **Data Storage**: All data, including texts, citations, and NLP annotations, is stored in JSON/JSONL format.

### Project Objectives
The objective of this project is to migrate from file-based JSON storage to a structured database system (PostgreSQL). Key goals include:
1. **Improved Data Storage**: Establish a structured database for hierarchical storage and efficient access to text divisions, citations, and NLP metadata.
2. **Enhanced Querying**: Enable efficient searching by term category, lemma, and citation location.
3. **Integration Support for NLP and LLMs**: Provide a data structure compatible with spaCy token attributes and AWS Bedrock LLM responses.
4. **Separation of Processing and Analysis Components**: Implement a **Toolkit** for batch processing of new texts and a user-facing **Application** for analysis, enhancing modularity and scalability.

---

## New System Architecture

### High-Level Architecture

1. **Frontend** (Unchanged):
   - Built with HTML5, Tailwind CSS, DaisyUI, and JavaScript (ES6+).
   - Interfaces with the FastAPI backend for dynamic interaction.

2. **Backend**:
   - **FastAPI**: Manages API endpoints for database access, searches, and LLM integration.
   - **Services Layer**: Handles interactions between the FastAPI endpoints and the database.
   - **Database Layer**:
     - **PostgreSQL 14+**: Used as the primary database with JSONB fields to store NLP annotations and term attributes.
     - **Redis** (Optional): For caching frequently accessed data.

3. **External Integrations**:
   - **AWS Bedrock (Claude-3)**: Continues to provide LLM-based analysis.
   - **spaCy**: Used for NLP preprocessing and token annotation.

---

### Tech Stack Overview

- **Retained Components**:
  - **Frontend**: HTML5, Tailwind CSS, DaisyUI, JavaScript.
  - **Backend**: FastAPI with Python 3.9+.
  - **LLM Integration**: AWS Bedrock (Claude-3-sonnet).

- **New Components**:
  - **Database**:
    - **PostgreSQL 14+** with JSONB for storing flexible, semi-structured data (e.g., NLP annotations).
    - **SQLAlchemy 2.0** for database modeling and async support.
    - **Alembic** for database migrations.
  - **API Layer**:
    - **asyncpg**: Async PostgreSQL driver.
    - **Dependency Injection in FastAPI**: For efficient and modular database connections.
  - **Caching**:
    - **Redis** (optional): Caches frequently accessed data, improving performance on common queries.

---

## System Component Separation

To meet our objectives, the system is divided into two primary components: **Text Processing Toolkit** and **Analysis Application**.

### 1. Text Processing Toolkit

- **Purpose**: Occasional batch processing for new text ingestion and database population.
- **Components**:
  - **Citation Parser**: Parses citation data (e.g., `[0057]` format) and maps them to text references.
  - **spaCy NLP Pipeline**: Processes texts, identifies terms, and annotates tokens.
  - **Database Loader**: Stores the processed data, including texts and NLP annotations, in PostgreSQL.
- **Workflow**:
  1. Process text files, parsing citation and text structure.
  2. Run NLP analysis with spaCy.
  3. Store results in PostgreSQL tables.
  
### 2. Analysis Application

- **Purpose**: Daily use by researchers for text retrieval, lemma analysis, and term categorization.
- **Components**:
  - **Text Search**: Retrieves text and terms by category, citation, or lemma.
  - **LLM Analysis Generation**: Integrates with AWS Bedrock for term summarization and analysis.
  - **Result Management**: Stores analysis outputs and contextual references in PostgreSQL.
- **Workflow**:
  1. Search for terms and citations by category.
  2. Gather contexts and pass them to AWS Bedrock for analysis.
  3. Store analysis results with citation and text links for further review.

---

## Database Schema Design

The database schema is structured to support the hierarchical, multilingual data and facilitate NLP and LLM workflows.

```sql
-- Core Tables for Text Storage
CREATE TABLE authors (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    normalized_name TEXT,
    language_code VARCHAR(5)
);

CREATE TABLE texts (
    id SERIAL PRIMARY KEY,
    author_id INTEGER REFERENCES authors,
    reference_code VARCHAR(20),
    title TEXT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE text_divisions (
    id SERIAL PRIMARY KEY,
    text_id INTEGER REFERENCES texts,
    book_number TEXT,
    chapter_number TEXT,
    section_number TEXT,
    page_number INTEGER,
    metadata JSONB
);

CREATE TABLE text_lines (
    id SERIAL PRIMARY KEY,
    division_id INTEGER REFERENCES text_divisions,
    line_number INTEGER,
    content TEXT,
    spacy_tokens JSONB,  -- Holds spaCy token data
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Analysis Storage for LLM and Lemmas
CREATE TABLE lemmas (
    id SERIAL PRIMARY KEY,
    lemma TEXT NOT NULL,
    language_code VARCHAR(5),
    category TEXT[],
    translations JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE lemma_analyses (
    id SERIAL PRIMARY KEY,
    lemma_id INTEGER REFERENCES lemmas,
    analysis_text TEXT,
    analysis_data JSONB,
    citations JSONB,
    created_by TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Key Points in the Schema Design

- **JSONB Columns**: Fields like `metadata` and `spacy_tokens` are JSONB, allowing for flexible storage of variable token attributes and custom metadata.
- **Relationships**: Tables are linked through foreign keys (e.g., `lemmas` to `lemma_analyses`, `text_divisions` to `text_lines`) to maintain referential integrity and streamline queries.
- **Indexes**: Create indexes on frequently queried fields like `lemma`, `category`, and token properties within `spacy_tokens`.

---

## Migration and Implementation Steps

### Phase 1: Setup & Infrastructure

1. **Database Setup**:
   - Install PostgreSQL and create a new database for the project.
   - Initialize Alembic for managing database migrations.
   
2. **Project Structure**:
   - Update the project structure to reflect the separation of toolkit and application, with directories for scripts, API endpoints, and services.

### Phase 2: Data Migration

1. **Data Extraction**:
   - Decie if it is better to crate data from scratch (txt extraction of data, parsing and converting metadata, running through spaCy NLP and storing the data and all token attributes)
   - According to decision, Write extraction scripts to load txt files, or migration of existing jsonl data , parse the according to current format conversions, and store it in the store it in the PostgreSQL tables defined in the schema.
   

2. **Testing**:
   - Verify the data migration by running sample queries on PostgreSQL to ensure data accuracy and consistency.

### Phase 3: Service Layer Implementation

1. **Text Service**:
   - Develop methods to retrieve and filter texts, lines, and citations by category, lemma, or other attributes.
   
2. **Analysis Service**:
   - Integrate AWS Bedrock for generating term analyses and summaries.
   - Store analyses with reference links to source texts and citations.

### Phase 4: API Layer Updates

- Update FastAPI routes to support the new database-based queries.
- Implement caching with Redis for frequently accessed terms and citation lookups.

### Phase 5: Frontend Integration

- Connect frontend queries to the updated API endpoints, supporting search and display of term categories, lemmas, and analysis results.

---

## Testing Strategy

1. **Unit Testing**:
   - Test individual service functions (e.g., text retrieval, lemma search) to ensure accuracy.
   
2. **Integration Testing**:
   - Verify end-to-end functionality between the backend and PostgreSQL, especially for key workflows like lemma lookup and citation retrieval.

3. **Load Testing**:
   - Assess database performance under realistic usage loads, optimizing indexes and caching as needed.

---

## Deployment Plan

- Deploy using Docker Compose, with services for PostgreSQL, Redis (if used), and the FastAPI backend.
- Configure environment variables and secure database access.
- Schedule routine backups for data integrity.

---

## Next Steps and Recommendations

1. **Schema Validation**: Finalize database schema based on real-world data queries and usage patterns.
2. **API Optimization**: Refine frequently used API endpoints for high performance.
3. **Toolkit and Application Documentation**: Document usage patterns for both the toolkit (batch processing) and application (real-time querying).
4. **Frontend Testing and Updates**: Ensure the frontend interface aligns with backend changes, especially for search and LLM analyses.

---

This guide provides a comprehensive plan to migrate to

 the new architecture, achieve separation between batch processing and daily analysis, and ensure data integrity and performance. If you need further clarification or additional details on any component, please feel free to ask.