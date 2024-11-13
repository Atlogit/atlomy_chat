# Merged Architecture Overview

## System Overview

The Ancient Medical Texts Analysis App is built on a modular, service-oriented architecture that emphasizes accuracy, performance, and maintainability. The system processes ancient medical texts through several specialized layers, each optimized for its specific function.

## Core Components

### 1. Work Structure System

The system uses TLG indexes to determine the correct structure for each work:

#### Work Structure Lookup
```python
# TLG_WORKS_INDEX format
{
    "0627": {
        "010": "De Articulis",
        # ... other works
    }
}

# TLG_MASTER_INDEX format
{
    "hippocrates": {
        "tlg_id": "TLG0627",
        "works": {
            "De Articulis": ["Section", "Line"],
            # ... other works
        }
    }
}
```

#### Structure Usage
```python
def _get_work_structure(author_id: str, work_id: str):
    # Get work name
    work_name = TLG_WORKS_INDEX.get(author_id, {}).get(work_id)
    if not work_name:
        return None
        
    # Find author entry
    author_entry = next(
        (entry for entry in TLG_MASTER_INDEX.values() 
         if entry.get("tlg_id") == f"TLG{author_id}"),
        None
    )
    if not author_entry:
        return None
        
    # Get work structure
    return author_entry["works"].get(work_name)
```

### 2. Corpus Processing System

The corpus processing system has been refactored into a modular, layered architecture for improved maintainability and separation of concerns. See [Corpus Processor Structure](corpus_processor_structure.md) for detailed documentation.

#### Component Hierarchy
```
CorpusBase
    └── CorpusCitation
        └── CorpusText
            └── CorpusNLP
                └── CorpusDB
                    └── CorpusProcessor
```

Each layer adds specific functionality:
- **CorpusBase**: Core initialization and shared resources
- **CorpusCitation**: Citation parsing and work structure handling
- **CorpusText**: Text line and sentence processing with structure-aware line numbers
- **CorpusNLP**: NLP processing and token management
- **CorpusDB**: Database operations
- **CorpusProcessor**: Main processing coordinator

Key features:
- Work structure-aware citation parsing
- Structure-based line numbering
- Improved citation accuracy
- Enhanced error handling and logging
- Progress tracking for long operations

### Data Models

#### Sentence Model
```python
class Sentence(Base):
    id: Mapped[int]
    content: Mapped[str]
    source_line_ids: Mapped[List[int]]
    start_position: Mapped[int]
    end_position: Mapped[int]
    spacy_data: Mapped[Optional[Dict[str, Any]]]
    categories: Mapped[List[str]]
    
    # Relationships
    text_lines = relationship("TextLine", secondary=sentence_text_lines)
    lexical_values = relationship("LexicalValue", back_populates="sentence")
```

#### Text Division Model
```python
class TextDivision(Base):
    id: Mapped[int]
    text_id: Mapped[int]
    author_id_field: Mapped[str]
    work_number_field: Mapped[str]
    author_name: Mapped[Optional[str]]
    work_name: Mapped[Optional[str]]
    volume: Mapped[Optional[str]]
    chapter: Mapped[Optional[str]]
    line: Mapped[Optional[str]]
    section: Mapped[Optional[str]]
    
    # Relationships
    text = relationship("Text", back_populates="divisions")
    lines = relationship("TextLine", back_populates="division")
```

#### Lexical Value Model
```python
class LexicalValue(Base):
    id = Column(UUID(as_uuid=True), primary_key=True)
    lemma = Column(String, unique=True, nullable=False)
    translation = Column(String)
    short_description = Column(Text)
    long_description = Column(Text)
    related_terms = Column(ARRAY(String))
    citations_used = Column(JSONB)
    references = Column(JSONB)
    sentence_contexts = Column(JSONB)
    
    # Relationships
    sentence_id = Column(Integer, ForeignKey('sentences.id'))
    sentence = relationship("Sentence", back_populates="lexical_values")
```

### 2. Service Layer

#### Corpus Service (Facade)
```python
class CorpusService:
    def __init__(self, session: AsyncSession):
        self.text_service = TextService(session)
        self.search_service = SearchService(session)
        self.category_service = CategoryService(session)
        
    async def list_texts(self) -> List[Dict]:
        return await self.text_service.list_texts()
        
    async def search_texts(
        self, 
        query: str,
        search_lemma: bool = False,
        categories: Optional[List[str]] = None
    ) -> List[Dict]:
        return await self.search_service.search_texts(
            query,
            search_lemma=search_lemma,
            categories=categories
        )
```

#### Text Service
```python
class TextService:
    async def list_texts(self) -> List[Dict]:
        # Efficient text preview using window functions
        preview_query = """
            WITH RankedLines AS (
                SELECT 
                    text_lines.content,
                    ROW_NUMBER() OVER (
                        PARTITION BY text_divisions.text_id 
                        ORDER BY text_divisions.id, text_lines.line_number
                    ) as rn
                FROM text_lines 
                JOIN text_divisions ON text_divisions.id = text_lines.division_id 
                WHERE text_divisions.text_id = :text_id
            )
            SELECT string_agg(content, E'\n') as preview
            FROM RankedLines 
            WHERE rn <= 3
        """
```

#### Lexical Service
```python
class LexicalService:
    def __init__(self, session: AsyncSession):
        self.llm_service = LLMService(session)
        self.citation_service = CitationService(session)
        self.json_storage = JSONStorageService()
        
    async def create_lexical_entry(
        self,
        lemma: str,
        search_lemma: bool = False
    ) -> Dict[str, Any]:
        # Get citations with enhanced sentence context
        citations = await self._get_citations(lemma, search_lemma)
        
        # Generate lexical value using LLM
        analysis = await self.llm_service.create_lexical_value(
            word=lemma,
            citations=citations
        )
        
        # Store in database and JSON
        entry = LexicalValue.from_dict(analysis)
        self.session.add(entry)
        await self.session.commit()
        
        # Cache the new entry
        await self._cache_value(lemma, entry.to_dict())
```

### 3. Search Service Architecture

#### Search Service Implementation
```python
class SearchService:
    async def search_texts(
        self, 
        query: str, 
        search_lemma: bool = False,
        categories: Optional[List[str]] = None,
        use_corpus_search: bool = True
    ) -> List[Dict]:
        # Choose appropriate query based on search type
        if use_corpus_search:
            if categories:
                search_query = CORPUS_CATEGORY_SEARCH
                params = {"category": categories[0]}
            elif search_lemma:
                search_query = CORPUS_LEMMA_SEARCH
                params = {"pattern": query}
            else:
                search_query = CORPUS_TEXT_SEARCH
                params = {"pattern": f'%{query}%'}
        else:
            if categories:
                search_query = CATEGORY_CITATION_QUERY
                params = {"category": categories[0]}
            elif search_lemma:
                search_query = LEMMA_CITATION_QUERY
                params = {"pattern": query}
            else:
                search_query = TEXT_CITATION_QUERY
                params = {"pattern": f'%{query}%'}
```

#### Search Result Formatting
```python
async def _format_citation_result(self, row: Dict, division: TextDivision) -> Dict:
    return {
        "sentence": {
            "id": str(row["sentence_id"]),
            "text": row["sentence_text"],
            "prev_sentence": row["prev_sentence"],
            "next_sentence": row["next_sentence"],
            "tokens": row["sentence_tokens"]
        },
        "citation": division.format_citation(),
        "context": {
            "line_id": str(row["line_id"]),
            "line_text": row["line_text"],
            "line_numbers": row["line_numbers"]
        },
        "location": {
            "volume": row["volume"],
            "chapter": row["chapter"],
            "section": row["section"]
        },
        "source": {
            "author": row["author_name"],
            "work": row["work_name"]
        }
    }
```

### 4. JSON Storage System

#### Directory Structure
```
lexical_values/
├── current/          # Current versions of lexical values
├── versions/         # Historical versions
└── backup/          # Automatic backups
```

#### Storage Service Implementation
```python
class JSONStorageService:
    def __init__(self, base_dir: str = "lexical_values"):
        self.base_dir = Path(base_dir)
        self._ensure_directory_structure()
    
    async def save(self, lemma: str, data: Dict[str, Any], create_version: bool = True):
        # Create backup of existing file
        self._create_backup(lemma)
        
        # Add metadata
        data["metadata"] = {
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "version": data.get("metadata", {}).get("version", "1.0")
        }
        
        # Save current version
        current_file = self._get_file_path(lemma)
        with open(current_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        # Create versioned copy if requested
        if create_version:
            version = datetime.now().strftime("%Y%m%d_%H%M%S")
            version_file = self._get_file_path(lemma, version)
            shutil.copy2(current_file, version_file)
```

### 5. Citation Service

#### Core Citation Query
```sql
WITH sentence_matches AS (
    SELECT DISTINCT ON (s.id)
        s.id as sentence_id,
        s.content as sentence_text,
        s.spacy_data as sentence_tokens,
        MIN(tl.line_number) as min_line_number,
        td.id as division_id,
        COALESCE(td.author_name, a.name) as author_name,
        COALESCE(td.work_name, t.title) as work_name,
        td.volume,
        td.chapter,
        td.section,
        -- Get previous and next sentences for context
        LAG(s.content) OVER (
            PARTITION BY td.id 
            ORDER BY MIN(tl.line_number)
        ) as prev_sentence,
        LEAD(s.content) OVER (
            PARTITION BY td.id 
            ORDER BY MIN(tl.line_number)
        ) as next_sentence
    FROM sentences s
    JOIN sentence_text_lines stl ON s.id = stl.sentence_id
    JOIN text_lines tl ON stl.text_line_id = tl.id
    JOIN text_divisions td ON tl.division_id = td.id
    JOIN texts t ON td.text_id = t.id
    LEFT JOIN authors a ON t.author_id = a.id
    WHERE {where_clause}
    GROUP BY 
        s.id, s.content,
        td.id, td.author_name, td.work_name,
        t.title, a.name,
        td.volume, td.chapter, td.section
)
SELECT * FROM sentence_matches
ORDER BY division_id, min_line_number
```

#### Specialized Citation Queries

1. **Direct Lemma Search**
```sql
WHERE token->>'lemma' = :pattern
```

2. **Text Content Search**
```sql
WHERE s.content ILIKE :pattern
```

3. **Category Search**
```sql
WHERE s.categories @> ARRAY[:category]::VARCHAR[]
```

4. **Citation Search**
```sql
WHERE td.author_id_field = :author_id 
  AND td.work_number_field = :work_number
```

#### Key Optimizations
- Window functions (`LAG`/`LEAD`) for efficient context retrieval
- JSON field searching for lemma lookups
- Array operations for category searches
- Coalesced author/work names
- Optimized joins with proper indexes

## Performance Optimizations

### 1. Efficient Text Preview
```sql
WITH RankedLines AS (
    SELECT 
        content,
        ROW_NUMBER() OVER (
            PARTITION BY text_divisions.text_id 
            ORDER BY text_divisions.id, text_lines.line_number
        ) as rn
    FROM text_lines 
    JOIN text_divisions ON text_divisions.id = text_lines.division_id 
    WHERE text_divisions.text_id = :text_id
)
SELECT string_agg(content, E'\n') as preview
FROM RankedLines 
WHERE rn <= 3
```

### 2. Optimized Relationships
- Selective loading with `joinedload` and `selectinload`
- Many-to-many relationship optimization with association tables
- Efficient citation retrieval using direct sentence queries

### 3. Caching Strategy
- Redis-based caching for frequently accessed data
- Version-aware caching for lexical values
- Configurable TTLs for different cache types
- Automatic cache invalidation on updates
## Implementation Status

### Completed Features
- [x] Enhanced citation system with author/work names
- [x] Efficient text preview generation
- [x] Redis-based caching system
- [x] JSON storage for lexical values
- [x] Service layer optimization
- [x] Direct sentence-based citation retrieval
- [x] Specialized LLM services for different tasks
- [x] Token counting and context length checking
- [x] Streaming support for lexical value generation
- [x] Bulk division fetching for citations
- [x] JSON storage with versioning and backups
- [x] Multiple search query types (corpus, lemma, category)
- [x] Optimized citation formatting

### In Progress
- [ ] Advanced search capabilities
- [ ] Real-time updates
- [ ] Enhanced monitoring
- [ ] Performance analytics

## Best Practices

### 1. Database Operations
- Use SQLAlchemy relationships for efficient joins
- Implement proper indexing on frequently queried fields
- Utilize window functions for efficient aggregations
- Maintain referential integrity with foreign keys

### 2. Caching Strategy
- Cache frequently accessed data
- Implement version-aware caching
- Use appropriate TTLs
- Handle cache invalidation properly

### 3. Error Handling
- Comprehensive logging
- Proper exception handling
- Clear error messages
- Graceful degradation

This architecture provides a robust foundation for the Ancient Medical Texts Analysis App, with clear paths for implementing planned enhancements while maintaining system reliability and performance. The modular design allows for independent scaling and optimization of components, while the comprehensive caching strategy ensures efficient operation at scale.