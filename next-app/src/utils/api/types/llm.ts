import { Citation } from './citation';

export interface AnalysisRequest {
  term: string;
  contexts: Array<{
    text: string;
    author?: string;
    reference?: string;
  }>;
  stream: boolean;
}

export interface AnalysisResponse {
  text: string;
  usage?: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
  model?: string;
}

export interface TokenCountResponse {
  count: number;
  within_limits: boolean;
  limit: number;
}

export interface QueryGenerationRequest {
  question: string;
  max_tokens?: number;
}

export interface PreciseQueryRequest {
  query_type: 'lemma_search' | 'category_search' | 'citation_search';
  parameters: {
    lemma?: string;
    category?: string;
    author_id?: string;
    work_number?: string;
    [key: string]: any;
  };
  max_tokens?: number;
}

export interface QueryResponse {
  sql: string;
  results: Citation[];
  usage: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
  model: string;
  raw_response?: Record<string, unknown>;
}
