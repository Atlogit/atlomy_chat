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
      let errorDetail = null;
      
      // Try to parse error response if it exists
      if (responseText) {
        try {
          const errorJson = JSON.parse(responseText);
          if (errorJson.error) {
            // Handle structured error object
            if (typeof errorJson.error === 'object') {
              errorMessage = errorJson.error.message || errorMessage;
              errorDetail = errorJson.error;
            } else {
              errorDetail = { message: errorJson.error };
            }
          } else if (errorJson.detail) {
            // Handle structured error details from backend
            if (typeof errorJson.detail === 'object') {
              errorMessage = errorJson.detail.message || errorMessage;
              errorDetail = errorJson.detail;
            } else {
              errorDetail = { message: errorJson.detail };
            }
          } else if (errorJson.message) {
            errorDetail = { message: errorJson.message };
          }
        } catch (e) {
          // If response is not JSON, use the raw text
          errorDetail = { message: responseText };
        }
      }

      // Special handling for 404 Not Found
      if (response.status === 404) {
        throw {
          message: 'Resource not found',
          status: 404,
          detail: errorDetail || { message: 'The requested resource could not be found' }
        } as ApiError;
      }

      throw {
        message: errorMessage,
        status: response.status,
        detail: errorDetail || { message: `Server returned status ${response.status}` }
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
        detail: {
          message: `Failed to parse response: ${responseText.substring(0, 100)}${responseText.length > 100 ? '...' : ''}`,
          error_type: 'parse_error'
        }
      } as ApiError;
    }
  } catch (error) {
    console.error('API Error:', error);
    
    // If it's already an ApiError, rethrow it
    if ((error as ApiError).message) {
      throw error as ApiError;
    }
    
    // Handle empty error objects or unknown errors
    throw {
      message: error instanceof Error ? error.message : 'An unexpected error occurred',
      status: 500,
      detail: error instanceof Error ? 
        { message: error.stack || error.message, error_type: 'unexpected_error' } : 
        typeof error === 'object' ? 
          (Object.keys(error || {}).length === 0 ? 
            { message: 'No error details available', error_type: 'empty_error' } : 
            { ...error, error_type: 'structured_error' }) : 
          { message: String(error), error_type: 'unknown_error' }
    } as ApiError;
  }
}
