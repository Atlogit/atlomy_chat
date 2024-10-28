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

    const responseText = await response.text();
    console.log('API Response Text:', responseText);

    if (!response.ok) {
      let errorMessage = `HTTP error! status: ${response.status}`;
      let errorDetail = '';
      
      try {
        const errorJson = JSON.parse(responseText);
        if (errorJson.detail) {
          errorDetail = errorJson.detail;
        }
      } catch (e) {
        // If response is not JSON, use the raw text
        errorDetail = responseText;
      }

      const error: ApiError = {
        message: errorMessage,
        status: response.status,
        detail: errorDetail
      };

      console.error('API Error:', error);
      console.error('Response details:', {
        status: response.status,
        statusText: response.statusText,
        headers: Object.fromEntries(response.headers.entries()),
        body: responseText,
      });
      throw error;
    }

    // Parse the response text as JSON
    let jsonResponse;
    try {
      jsonResponse = responseText ? JSON.parse(responseText) : null;
    } catch (parseError) {
      console.error('Error parsing JSON response:', parseError);
      console.error('Raw response:', responseText);
      throw new Error('Invalid JSON response from server');
    }

    onProgress?.('Finalizing results...');

    return jsonResponse as T;
  } catch (error) {
    console.error('API Error:', error);
    if (error instanceof Error) {
      console.error('Error details:', {
        name: error.name,
        message: error.message,
        stack: error.stack,
      });
      throw {
        message: error.message,
        status: (error as ApiError).status,
        detail: (error as ApiError).detail
      };
    }
    throw { message: 'An unknown error occurred', details: JSON.stringify(error) };
  }
}

export function formatResults(data: unknown): string {
  try {
    return typeof data === 'string' ? data : JSON.stringify(data, null, 2);
  } catch (error) {
    return `Error formatting results: ${(error as Error).message}`;
  }
}

// Enhanced types for the new database schema
export interface TextDivision {
  id: string;
  // Citation components
  author_id_field: string;
  work_number_field: string;
  epithet_field?: string;
  fragment_field?: string;
  // Structural components
  volume?: string;
  chapter?: string;
  line?: string;
  section?: string;
  // Title components
  is_title: boolean;
  title_number?: string;
  title_text?: string;
  // Additional data
  metadata?: Record<string, unknown>;
  lines: TextLine[];
}

export interface TextLine {
  line_number: number;
  content: string;
  categories: string[];
  spacy_tokens?: Record<string, unknown>;
}

export interface Text {
  id: string;
  title: string;
  author?: string;
  reference_code?: string;
  metadata?: Record<string, unknown>;
  divisions?: TextDivision[];
}

export interface SearchResult {
  text_id: string;
  text_title: string;
  author?: string;
  division: {
    author_id_field: string;
    work_number_field: string;
    epithet_field?: string;
    fragment_field?: string;
    volume?: string;
    chapter?: string;
    line?: string;
    section?: string;
    is_title: boolean;
    title_number?: string;
    title_text?: string;
  };
  line_number: number;
  content: string;
  categories: string[];
  spacy_data?: Record<string, unknown>;
}

export interface LexicalValue {
  lemma: string;
  translation: string;
  references?: string[];
}

export interface TextSearchRequest {
  query: string;
  searchLemma?: boolean;
  categories?: string[];
}

export interface LexicalBatchCreateRequest {
  words: string[];
  searchLemma?: boolean;
}

export interface LexicalBatchUpdateRequest {
  updates: Array<{
    lemma: string;
    translation: string;
  }>;
}

export interface CreateResponse {
  task_id: string;
  message: string;
}

export interface TaskStatus {
  status: 'in_progress' | 'completed' | 'error';
  success?: boolean;
  message: string;
  entry?: LexicalValue;
  action?: 'create' | 'update';
}

// API endpoints
export const API = {
  llm: {
    query: '/api/v1/llm/query',
  },
  lexical: {
    create: '/api/v1/lexical/create',
    batchCreate: '/api/v1/lexical/batch-create',
    get: (lemma: string) => `/api/v1/lexical/get/${encodeURIComponent(lemma)}`,
    list: '/api/v1/lexical/list',
    update: '/api/v1/lexical/update',
    batchUpdate: '/api/v1/lexical/batch-update',
    delete: (lemma: string) => `/api/v1/lexical/delete/${encodeURIComponent(lemma)}`,
    status: (taskId: string) => `/api/v1/lexical/status/${encodeURIComponent(taskId)}`,
  },
  corpus: {
    list: '/api/v1/corpus/list',
    search: '/api/v1/corpus/search',
    all: '/api/v1/corpus/all',
    text: (id: string) => `/api/v1/corpus/text/${encodeURIComponent(id)}`,
    category: (category: string) => `/api/v1/corpus/category/${encodeURIComponent(category)}`,
  },
};
