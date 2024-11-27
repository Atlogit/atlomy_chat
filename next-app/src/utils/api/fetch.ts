import { ApiError } from './types/types';

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
      console.log('API Response Text Length:', responseText.length);
    } catch (e) {
      console.error('Error reading response text:', e);
      throw {
        message: 'Failed to read response from server',
        status: response.status,
        detail: {
          message: e instanceof Error ? e.message : 'Unknown error reading response',
          error_type: 'parse_error',
          raw_error: e instanceof Error ? e.stack : String(e)
        }
      } as ApiError;
    }

    // Enhanced progress tracking for large responses
    const updateProgress = (stage: string, current?: number, total?: number) => {
      let progressStage = stage;
      if (current !== undefined && total !== undefined) {
        progressStage += ` (${current}/${total})`;
      }
      onProgress?.(progressStage);
    };

    // Handle non-ok responses
    if (!response.ok) {
      let errorMessage = `HTTP error! status: ${response.status}`;
      let errorDetail: ApiError['detail'] = { 
        message: errorMessage,
        error_type: 'unknown_error'
      };
      
      // Try to parse error response if it exists
      if (responseText) {
        try {
          const errorJson = JSON.parse(responseText);
          
          // Handle different error response structures
          if (errorJson.error) {
            errorMessage = errorJson.error.message || errorMessage;
            errorDetail = {
              message: errorJson.error.message || errorMessage,
              error_type: errorJson.error.error_type || 'unknown_error',
              sql_query: errorJson.error.sql_query,
              row_count: errorJson.error.row_count,
              raw_error: JSON.stringify(errorJson.error)
            };
          } else if (errorJson.detail) {
            // Handle structured error details from backend
            errorMessage = typeof errorJson.detail === 'string' 
              ? errorJson.detail 
              : errorJson.detail.message || errorMessage;
            
            errorDetail = typeof errorJson.detail === 'string'
              ? { 
                  message: errorMessage, 
                  error_type: 'unknown_error',
                  raw_error: responseText 
                }
              : {
                  message: errorJson.detail.message || errorMessage,
                  error_type: errorJson.detail.error_type || 'unknown_error',
                  sql_query: errorJson.detail.sql_query,
                  row_count: errorJson.detail.row_count,
                  raw_error: responseText
                };
          } else if (errorJson.message) {
            errorDetail = { 
              message: errorJson.message,
              error_type: 'unknown_error',
              raw_error: responseText
            };
          }
        } catch (e) {
          // If response is not JSON, use the raw text
          errorDetail = { 
            message: responseText,
            error_type: 'parse_error',
            raw_error: `Parse error: ${e instanceof Error ? e.message : String(e)}`
          };
        }
      }

      // Throw structured ApiError with comprehensive logging
      const apiError = {
        message: errorMessage,
        status: response.status,
        detail: errorDetail
      } as ApiError;

      console.error('Structured API Error:', JSON.stringify(apiError, null, 2));
      throw apiError;
    }

    // Handle empty but successful responses
    if (!responseText || !responseText.trim()) {
      console.log('Empty but successful response');
      updateProgress('Finalizing results', 1, 1);
      return null as unknown as T;
    }

    // Parse non-empty responses
    try {
      const jsonResponse = JSON.parse(responseText);
      
      // Additional progress tracking for parsed response
      if (Array.isArray(jsonResponse)) {
        updateProgress('Parsing results', jsonResponse.length, jsonResponse.length);
        console.log(`Parsed ${jsonResponse.length} results`);
      } else if (jsonResponse && typeof jsonResponse === 'object') {
        const keys = Object.keys(jsonResponse);
        updateProgress('Parsing results', keys.length, keys.length);
      }

      updateProgress('Finalizing results', 1, 1);
      return jsonResponse as T;
    } catch (parseError) {
      console.error('Error parsing JSON response:', parseError);
      console.error('Raw response (first 500 chars):', responseText.substring(0, 500));
      
      // Create a detailed parse error
      const parseApiError: ApiError = {
        message: 'Invalid JSON response from server',
        status: 500,
        detail: {
          message: `Failed to parse response: ${responseText.substring(0, 100)}${responseText.length > 100 ? '...' : ''}`,
          error_type: 'parse_error',
          raw_error: responseText
        }
      };

      console.error('Parse Error Details:', JSON.stringify(parseApiError, null, 2));
      throw parseApiError;
    }
  } catch (error) {
    console.error('Catch-all API Error:', error);
    
    // If it's already an ApiError, rethrow it
    if (error && typeof error === 'object' && 'message' in error) {
      console.error('Existing ApiError:', JSON.stringify(error, null, 2));
      throw error as ApiError;
    }
    
    // Create a comprehensive fallback error
    const fallbackError: ApiError = {
      message: 'Unexpected API request failure',
      status: 500,
      detail: {
        message: error instanceof Error 
          ? error.message || 'Unknown error occurred' 
          : typeof error === 'string' 
            ? error 
            : 'An unhandled error occurred',
        error_type: 'unexpected_error',
        // Include stringified error for debugging
        raw_error: JSON.stringify(error)
      }
    };

    console.error('Fallback Error:', JSON.stringify(fallbackError, null, 2));
    throw fallbackError;
  }
}
