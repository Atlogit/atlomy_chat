interface ApiError {
  message: string;
  status?: number;
  detail?: string;
}

export async function fetchApi<T>(
  endpoint: string,
  options: RequestInit = {},
  onProgress?: (stage: string) => void
): Promise<T> {
  try {
    console.log('API Request:', { endpoint, options });

    onProgress?.('Sending request...');

    const response = await fetch(endpoint, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    console.log('API Response Status:', response.status);

    onProgress?.('Processing response...');

    let responseText: string;
    try {
      responseText = await response.text();
      console.log('API Response Text:', responseText);
    } catch (e) {
      console.error('Error reading response text:', e);
      throw {
        message: 'Failed to read response from server',
        status: response.status,
        detail: e instanceof Error ? e.message : 'Unknown error reading response'
      } as ApiError;
    }

    // Handle non-ok responses
    if (!response.ok) {
      let errorMessage = `HTTP error! status: ${response.status}`;
      let errorDetail = '';
      
      // Try to parse error response if it exists
      if (responseText) {
        try {
          const errorJson = JSON.parse(responseText);
          if (errorJson.detail) {
            errorDetail = errorJson.detail;
          } else if (errorJson.message) {
            errorDetail = errorJson.message;
          }
        } catch (e) {
          // If response is not JSON, use the raw text
          errorDetail = responseText;
        }
      }

      // Special handling for 404 Not Found
      if (response.status === 404) {
        throw {
          message: 'Resource not found',
          status: 404,
          detail: errorDetail || 'The requested resource could not be found'
        } as ApiError;
      }

      throw {
        message: errorMessage,
        status: response.status,
        detail: errorDetail || `Server returned status ${response.status}`
      } as ApiError;
    }

    // Handle empty but successful responses
    if (!responseText || !responseText.trim()) {
      console.log('Empty but successful response');
      return null as unknown as T;
    }

    // Parse non-empty responses
    try {
      const jsonResponse = JSON.parse(responseText);
      onProgress?.('Finalizing results...');
      return jsonResponse as T;
    } catch (parseError) {
      console.error('Error parsing JSON response:', parseError);
      console.error('Raw response:', responseText);
      throw {
        message: 'Invalid JSON response from server',
        detail: `Failed to parse response: ${responseText.substring(0, 100)}${responseText.length > 100 ? '...' : ''}`
      } as ApiError;
    }
  } catch (error) {
    console.error('API Error:', error);
    
    // If it's already an ApiError, rethrow it
    if ((error as ApiError).status !== undefined || (error as ApiError).message) {
      throw error as ApiError;
    }
    
    // Handle empty error objects
    if (error && Object.keys(error).length === 0) {
      throw {
        message: 'An unexpected error occurred',
        status: 500,
        detail: 'No error details available'
      } as ApiError;
    }
    
    // Otherwise wrap it in an ApiError
    throw {
      message: error instanceof Error ? error.message : 'An unknown error occurred',
      status: 500,
      detail: error instanceof Error ? error.stack : 
             typeof error === 'object' ? JSON.stringify(error) : String(error)
    } as ApiError;
  }
}

// Type for UUID
export type UUID = string;

// LLM Analysis Types
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

// Citation Types
export interface Citation {
  sentence: {
    id: string;
    text: string;
    prev_sentence?: string;
    next_sentence?: string;
    tokens?: Record<string, any>;
  };
  citation: string;
  context: {
    line_id: string;
    line_text: string;
    line_numbers: number[];
  };
  location: {
    volume?: string;
    chapter?: string;
    section?: string;
  };
  source: {
    author: string;
    work: string;
  };
}

// Lexical Value Types
export interface LemmaAnalysis {
  id: UUID;
  analysis_text: string;
  analysis_data?: Record<string, any>;
  citations?: Record<string, any>;
  created_by: string;
}

export interface LexicalValue {
  id: UUID;
  lemma: string;
  language_code?: string;
  categories: string[];
  translations?: Record<string, any>;
  translation?: string;
  short_description?: string;
  long_description?: string;
  related_terms?: string[];
  citations_used?: Citation[];
  analyses: LemmaAnalysis[];
  created_at: string;
  updated_at: string;
  version: string;
}

export interface LemmaCreate {
  lemma: string;
  searchLemma?: boolean;
  language_code?: string;
  categories?: string[];
  translations?: Record<string, any>;
  analyze?: boolean;
}

export interface LemmaBatchCreate {
  lemmas: LemmaCreate[];
}

export interface BatchCreateResponse {
  successful: LexicalValue[];
  failed: Array<{
    lemma: string;
    error: string;
  }>;
  total: number;
}

export interface CreateResponse {
  task_id: UUID;
  message: string;
}

export interface TaskStatus {
  status: 'in_progress' | 'completed' | 'error';
  message: string;
  entry?: LexicalValue;
  action?: 'create' | 'update';
}

export interface DeleteTriggerResponse {
  trigger_id: string;
  message: string;
  entry: LexicalValue;
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
  results: Citation[];  // Updated to use Citation type instead of any[]
  usage: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
  model: string;
  raw_response?: Record<string, unknown>;
}

// API endpoints
export const API = {
  llm: {
    analyze: '/api/v1/llm/analyze',
    analyzeStream: '/api/v1/llm/analyze/stream',
    tokenCount: '/api/v1/llm/token-count',
    generateQuery: '/api/v1/llm/generate-query',
    generatePreciseQuery: '/api/v1/llm/generate-precise-query',
  },
  lexical: {
    create: '/api/v1/lexical/create',
    batchCreate: '/api/v1/lexical/batch-create',
    get: (lemma: string) => `/api/v1/lexical/get/${encodeURIComponent(lemma)}`,
    list: '/api/v1/lexical/list',
    update: '/api/v1/lexical/update',
    batchUpdate: '/api/v1/lexical/batch-update',
    delete: (lemma: string) => `/api/v1/lexical/delete/${encodeURIComponent(lemma)}`,
    deleteTrigger: (lemma: string) => `/api/v1/lexical/delete/${encodeURIComponent(lemma)}/trigger`,
    status: (taskId: UUID) => `/api/v1/lexical/status/${encodeURIComponent(taskId)}`,
    versions: (lemma: string) => `/api/v1/lexical/versions/${encodeURIComponent(lemma)}`,
  },
  corpus: {
    list: '/api/v1/corpus/list',
    search: '/api/v1/corpus/search',
    all: '/api/v1/corpus/all',
    text: (id: string) => `/api/v1/corpus/text/${encodeURIComponent(id)}`,
    category: (category: string) => `/api/v1/corpus/category/${encodeURIComponent(category)}`,
  },
};
