# Service Layer Structure

## Recent Changes

The corpus service layer has been refactored into specialized services to improve performance and maintainability. This document outlines the new structure and its benefits.

## Directory Structure

```
app/services/
├── corpus_service.py     # Main facade service
├── text_service.py       # Text operations
├── search_service.py     # Search functionality
└── category_service.py   # Category operations
```

## Service Responsibilities

### 1. Corpus Service (Facade)
- **Purpose**: Coordinates between specialized services
- **Key Methods**:
  - `list_texts()`: Get text list with metadata
  - `get_text_by_id(text_id)`: Get specific text
  - `get_all_texts()`: Get all texts with content
  - `search_texts(query, search_lemma, categories)`: Search functionality
  - `search_by_category(category)`: Category search
  - `invalidate_text_cache(text_id)`: Cache management

### 2. Text Service
- **Purpose**: Core text operations and content management
- **Key Features**:
  - Optimized text preview using window functions
  - Efficient metadata loading
  - Selective line content loading
  - Redis caching integration
- **Key Methods**:
  - `list_texts()`: Get texts with previews
  - `get_text_by_id()`: Get full text content
  - `get_all_texts()`: Get complete corpus

### 3. Search Service
- **Purpose**: Text search operations
- **Key Features**:
  - Content search
  - Lemma search support
  - Category-based search
  - Citation formatting
- **Key Methods**:
  - `search_texts()`: Multi-mode search
  - `_format_citation_result()`: Citation formatting

### 4. Category Service
- **Purpose**: Category-specific operations
- **Key Features**:
  - Category-based text retrieval
  - Citation formatting
  - Category result caching
- **Key Methods**:
  - `search_by_category()`: Category search
  - `_format_citation_result()`: Citation formatting

## Performance Improvements

### Text Preview Optimization
- Uses SQL window functions for efficient preview loading:
```sql
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
```

### Caching Strategy
- **Text List Cache**:
  - Key: `{TEXT_CACHE_PREFIX}list`
  - Content: Text metadata and previews
  - TTL: Configurable via settings

- **Individual Text Cache**:
  - Key: `{TEXT_CACHE_PREFIX}{text_id}`
  - Content: Complete text with divisions and lines
  - TTL: Configurable via settings

- **Search Cache**:
  - Key: `{SEARCH_CACHE_PREFIX}{query}_{search_lemma}_{categories}`
  - Content: Search results with citations
  - TTL: Configurable via settings

- **Category Cache**:
  - Key: `{CATEGORY_CACHE_PREFIX}{category}`
  - Content: Category search results
  - TTL: Configurable via settings

## Data Flow Examples

### Text Listing Flow
1. Request hits `/list` endpoint
2. CorpusService delegates to TextService
3. TextService:
   ```python
   async def list_texts(self):
       cache_key = await self._cache_key("text", "list")
       cached_data = await self.redis.get(cache_key)
       if cached_data:
           return cached_data
       
       # Efficient query with preview generation
       # Cache results
       return data
   ```

### Search Flow
1. Request hits `/search` endpoint
2. CorpusService delegates to SearchService
3. SearchService:
   ```python
   async def search_texts(self, query, search_lemma=False, categories=None):
       cache_key = self._generate_search_cache_key(query, search_lemma, categories)
       cached_data = await self.redis.get(cache_key)
       if cached_data:
           return cached_data
           
       # Execute appropriate search query
       # Format results with citations
       # Cache results
       return data
   ```

## Benefits

1. **Maintainability**:
   - Clear separation of concerns
   - Each service under 150 lines
   - Focused responsibility
   - Easier testing and debugging

2. **Performance**:
   - Optimized preview loading
   - Efficient caching
   - Reduced database queries
   - Minimized data transfer

3. **Scalability**:
   - Independent service scaling
   - Isolated caching strategies
   - Easy to add new features
   - Modular testing

## Migration Notes

1. **API Compatibility**:
   - Maintained existing API interface
   - No changes needed in frontend
   - Backward compatible responses

2. **Cache Migration**:
   - Clear all caches after deployment
   - New caching strategy takes effect automatically

3. **Performance Monitoring**:
   - Monitor SQL query patterns
   - Watch cache hit rates
   - Track response times
