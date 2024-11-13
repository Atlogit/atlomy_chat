import { useState, useCallback } from 'react';
import { fetchApi } from '../utils/api';

interface ApiError {
  message: string;
  status?: number;
  detail?: string | { message: string; error_type?: string };
}

interface ApiHookResult<T> {
  data: T | null;
  error: ApiError | null;
  isLoading: boolean;
  progress: { current: number; total: number };
  execute: (endpoint: string, options?: RequestInit, timeout?: number) => Promise<T | null>;
}

const DEFAULT_TIMEOUT = 300000; // 5 minutes
const MAX_RETRIES = 0;
const INITIAL_BACKOFF = 1000; // 1 second

export function useApi<T>(): ApiHookResult<T> {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<ApiError | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [progress, setProgress] = useState<{ current: number; total: number }>({ current: 0, total: 0 });

  const execute = useCallback(async (endpoint: string, options?: RequestInit, timeout: number = DEFAULT_TIMEOUT): Promise<T | null> => {
    setIsLoading(true);
    setError(null);
    setData(null); // Clear previous data when starting new request
    setProgress({ current: 0, total: 0 });

    let retries = 0;

    while (retries <= MAX_RETRIES) {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), timeout);

      try {
        const result = await fetchApi<T>(endpoint, {
          ...options,
          signal: controller.signal
        }, (stage: string) => {
          // Parse progress from stage string if available
          const match = stage.match(/(\d+)\/(\d+)/);
          if (match) {
            setProgress({ current: parseInt(match[1]), total: parseInt(match[2]) });
          }
        });

        if (result !== null) {  // Only set data if we got a valid result
          setData(result);
        }
        
        setIsLoading(false);
        clearTimeout(timeoutId);
        return result;
      } catch (err) {
        console.error(`API Error (attempt ${retries + 1}):`, err);
        clearTimeout(timeoutId);
        
        if (retries === MAX_RETRIES) {
          // Enhanced error handling
          let apiError: ApiError;
          
          if (!err || (typeof err === 'object' && Object.keys(err).length === 0)) {
            // Handle empty error case
            apiError = {
              message: 'API request failed',
              status: 500,
              detail: {
                message: 'The server returned an empty response or no error details',
                error_type: 'empty_response'
              }
            };
          } else if ((err as ApiError).message) {
            // Handle pre-formatted API errors
            apiError = err as ApiError;
          } else if (err instanceof Error) {
            // Handle standard JS errors
            apiError = {
              message: err.message,
              detail: {
                message: err.stack || err.message,
                error_type: 'js_error'
              }
            };
          } else if (typeof err === 'object') {
            // Handle structured error responses
            const errorObj = err as Record<string, any>;
            apiError = {
              message: errorObj.message || 'An unknown error occurred',
              status: errorObj.status,
              detail: typeof errorObj.detail === 'object' 
                ? errorObj.detail
                : { 
                    message: errorObj.detail || JSON.stringify(errorObj),
                    error_type: 'structured_error'
                  }
            };
          } else {
            // Handle any other type of error
            apiError = {
              message: 'An unknown error occurred',
              detail: {
                message: String(err),
                error_type: 'unknown_error'
              }
            };
          }
          
          setError(apiError);
          setIsLoading(false);
          return null;
        }

        // Exponential backoff for retries
        const backoff = INITIAL_BACKOFF * Math.pow(2, retries);
        await new Promise(resolve => setTimeout(resolve, backoff));
        
        retries++;
      }
    }

    setIsLoading(false);
    return null;
  }, []);

  return { data, error, isLoading, progress, execute };
}
