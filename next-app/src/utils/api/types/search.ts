import { CitationObject } from './citation';

/**
 * Metadata for queries that return no results
 */
export interface NoResultsMetadata {
  original_question: string;
  generated_query: string;
  search_description: string;
  search_criteria: Record<string, string>;
}

/**
 * Request model for text search operations
 */
export interface TextSearchRequest {
  query: string;
  search_lemma?: boolean;
  categories?: string[];
}

/**
 * Request model for query generation
 */
export interface QueryGenerationRequest {
  question: string;
  max_tokens?: number;
}

/**
 * Request model for paginated results
 */
export interface PaginationRequest {
  results_id: string;
  page: number;
  page_size: number;
}

/**
 * Response model for search operations
 * Contains both results and pagination metadata
 */
export interface SearchResponse {
  results: CitationObject[];
  results_id: string;
  total_results: number;
  no_results_metadata?: NoResultsMetadata;
}

/**
 * Response model for paginated results
 */
export interface PaginatedResponse {
  results: CitationObject[];
  page: number;
  page_size: number;
  total_results: number;
  no_results_metadata?: NoResultsMetadata;
}

/**
 * Response model for natural language query operations
 */
export interface QueryResponse {
  sql: string;
  results: CitationObject[];
  results_id: string;
  total_results: number;
  error?: string;
  no_results_metadata?: NoResultsMetadata;
}

export type SearchResult = CitationObject;
