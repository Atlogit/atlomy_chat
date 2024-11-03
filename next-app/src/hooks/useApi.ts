import { useState, useCallback } from 'react';
import { fetchApi } from '../utils/api';

interface ApiError {
  message: string;
  status?: number;
  detail?: string;
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
          // Format error object
          let apiError: ApiError;
          if ((err as ApiError).message) {
            apiError = err as ApiError;
          } else if (err instanceof Error) {
            apiError = {
              message: err.message,
              detail: err.stack
            };
          } else if (typeof err === 'object' && err !== null) {
            // Handle structured error responses
            const errorObj = err as Record<string, any>;
            
            // Handle empty error object case
            if (Object.keys(errorObj).length === 0) {
              apiError = {
                message: 'An error occurred while processing your request',
                detail: 'No additional error details available'
              };
            } else {
              apiError = {
                message: errorObj.message || 'An unknown error occurred',
                status: errorObj.status,
                detail: typeof errorObj.detail === 'object' 
                  ? JSON.stringify(errorObj.detail, null, 2)
                  : errorObj.detail || JSON.stringify(errorObj)
              };
            }
          } else {
            apiError = {
              message: 'An unknown error occurred',
              detail: String(err)
            };
          }
          
          setError(apiError);
          setIsLoading(false);
          return null;
        }

        // Exponential backoff
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
