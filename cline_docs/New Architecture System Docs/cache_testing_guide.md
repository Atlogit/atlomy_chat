# Redis Caching Implementation Testing Guide

## Cache Configuration
- Redis URL: redis://localhost:6379
- Database: 0
- Cache TTLs:
  - Text cache: 24 hours
  - Search cache: 30 minutes
  - Default cache: 1 hour

## Cache Keys and Prefixes
- Text data: `text:{id}`
- Search results: `search:{params}`
- Category results: `category:{name}`

## Testing Scenarios

### 1. Text List Caching
- Endpoint: `GET /api/v1/corpus/texts`
- Cache Key: `text:list`
- TTL: 24 hours
- Expected Behavior:
  - First request: Database query + cache store
  - Subsequent requests within TTL: Return cached data
  - After TTL: Re-query database

### 2. Individual Text Caching
- Endpoint: `GET /api/v1/corpus/texts/{id}`
- Cache Key: `text:{id}`
- TTL: 24 hours
- Expected Behavior:
  - First request: Database query + cache store
  - Subsequent requests within TTL: Return cached data
  - Cache includes full text data with divisions and lines

### 3. Search Results Caching
- Endpoint: `POST /api/v1/corpus/search`
- Cache Key: `search:{query_params}`
- TTL: 30 minutes
- Parameters to test:
  - Text search
  - Lemma search
  - Category filtering
- Expected Behavior:
  - Unique cache keys for different search parameters
  - Shorter TTL due to result volatility

### 4. Category Search Caching
- Endpoint: `GET /api/v1/corpus/category/{name}`
- Cache Key: `category:{name}`
- TTL: 30 minutes
- Expected Behavior:
  - Category-specific result caching
  - Efficient retrieval for common categories

### 5. Cache Invalidation
- Function: `invalidate_text_cache()`
- Scenarios to test:
  - Single text invalidation
  - Full cache invalidation
  - Pattern-based invalidation
- Expected Behavior:
  - Specific text: Only invalidate related keys
  - Full invalidation: Clear all text-related caches

## Frontend Integration Testing

### 1. ListTexts Component
- Should handle cached text list efficiently
- Loading states during cache misses
- Error handling for failed cache/database operations

### 2. TextDisplay Component
- Should display cached text data
- Handle cache misses gracefully
- Show loading states during database queries

### 3. SearchForm Component
- Should use cached search results when available
- Generate proper cache keys based on search parameters
- Handle cache invalidation for new searches

### 4. Performance Considerations
- Monitor Redis memory usage
- Track cache hit/miss ratios
- Measure response times:
  - Cache hits vs. database queries
  - Search operation performance
  - Category filtering speed

## Error Handling
- Redis connection failures
- Cache miss scenarios
- Invalid cache data
- Database fallback behavior

## Monitoring and Maintenance
- Regular cache size monitoring
- TTL effectiveness review
- Cache hit rate analysis
- Memory usage optimization

## Cache Optimization Opportunities
1. Implement cache warming for frequently accessed texts
2. Adjust TTLs based on usage patterns
3. Consider implementing cache compression for large texts
4. Monitor and optimize cache key patterns

## Testing Tools
- Redis CLI monitoring
- API endpoint testing
- Frontend performance monitoring
- Database query logging

## Next Steps
1. Implement automated cache testing
2. Set up cache monitoring metrics
3. Document cache performance baselines
4. Create cache maintenance procedures
