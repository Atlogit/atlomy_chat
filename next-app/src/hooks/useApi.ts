import { useState, useCallback } from 'react';
import { fetchApi } from '../utils/api';
import { ApiError } from '../utils/api/types/types';

// Enhanced debugging configuration
const DEBUG_CONFIG = {
  NATURAL_LANGUAGE_QUERY: true,
  GENERAL_API_CALLS: false,
  PROGRESS_TRACKING: true
};

interface ApiProgress {
  current: number;
  total: number;
  percentage: number;
  stage?: string;
}

interface ApiHookResult<T> {
  data: T | null;
  error: ApiError | null;
  isLoading: boolean;
  progress: ApiProgress;
  execute: (endpoint: string, options?: RequestInit, timeout?: number) => Promise<T | null>;
  cancelRequest: () => void;
  retry: () => Promise<T | null>;
}

const DEFAULT_TIMEOUT = 600000; // 10 minutes
const MAX_RETRIES = 3;
const INITIAL_BACKOFF = 1000; // 1 second

export function useApi<T>(): ApiHookResult<T> {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<ApiError | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [progress, setProgress] = useState<ApiProgress>({ 
    current: 0, 
    total: 0, 
    percentage: 0,
    stage: 'Initializing'
  });
  const [abortController, setAbortController] = useState<AbortController | null>(null);
  
  // Store last request details for retry
  const [lastRequest, setLastRequest] = useState<{
    endpoint: string;
    options?: RequestInit;
    timeout?: number;
  } | null>(null);

  const cancelRequest = useCallback(() => {
    if (abortController) {
      abortController.abort();
      setIsLoading(false);
      setProgress({ current: 0, total: 0, percentage: 0, stage: 'Cancelled' });
    }
  }, [abortController]);

  const retry = useCallback(async () => {
    if (!lastRequest) {
      console.error('No previous request to retry');
      return null;
    }

    // Reset error state
    setError(null);

    // Execute the last request
    return execute(
      lastRequest.endpoint, 
      lastRequest.options, 
      lastRequest.timeout
    );
  }, [lastRequest]);

  const execute = useCallback(async (
    endpoint: string, 
    options?: RequestInit, 
    timeout: number = DEFAULT_TIMEOUT
  ): Promise<T | null> => {
    // Enhanced debugging for specific query types
    const isNaturalLanguageQuery = endpoint.includes('/generate-query');
    
    if (DEBUG_CONFIG.NATURAL_LANGUAGE_QUERY && isNaturalLanguageQuery) {
      console.group('🔍 Natural Language Query Debug');
      console.log('Endpoint:', endpoint);
      console.log('Options:', JSON.stringify(options, null, 2));
      console.groupEnd();
    }

    // Reset state
    setIsLoading(true);
    setError(null);
    setData(null);
    
    // Store request details for potential retry
    setLastRequest({ endpoint, options, timeout });
    
    // Create new abort controller
    const controller = new AbortController();
    setAbortController(controller);

    // Set initial progress
    setProgress({ 
      current: 0, 
      total: 0, 
      percentage: 0,
      stage: 'Starting request'
    });

    // Timeout handler
    const timeoutId = setTimeout(() => {
      controller.abort();
    }, timeout);

    let retries = 0;

    while (retries <= MAX_RETRIES) {
      try {
        const result = await fetchApi<T>(
          endpoint, 
          {
            ...options,
            signal: controller.signal
          }, 
          (progressInfo: string) => {
            // Enhanced progress tracking
            if (DEBUG_CONFIG.PROGRESS_TRACKING) {
              console.log('Progress:', progressInfo);
            }

            // Parse progress information
            try {
              const progressData = JSON.parse(progressInfo);
              const current = progressData.current || 0;
              const total = progressData.total || 0;
              const percentage = total > 0 ? Math.round((current / total) * 100) : 0;

              setProgress({
                current,
                total,
                percentage,
                stage: progressData.stage || 'Processing'
              });
            } catch {
              // Fallback for simple string progress
              const match = progressInfo.match(/(\d+)\/(\d+)/);
              if (match) {
                const current = parseInt(match[1]);
                const total = parseInt(match[2]);
                const percentage = total > 0 ? Math.round((current / total) * 100) : 0;

                setProgress({
                  current,
                  total,
                  percentage,
                  stage: 'Processing'
                });
              }
            }
          }
        );

        // Clear timeout and reset loading state
        clearTimeout(timeoutId);
        setIsLoading(false);
        setProgress({ 
          current: 100, 
          total: 100, 
          percentage: 100,
          stage: 'Completed' 
        });

        // Debugging for query results
        if (DEBUG_CONFIG.NATURAL_LANGUAGE_QUERY && isNaturalLanguageQuery && result) {
          console.group('✅ Query Results');
          console.log('Result Type:', typeof result);
          console.log('Result Keys:', Object.keys(result as object));
          console.log('Full Result:', JSON.stringify(result, null, 2));
          console.groupEnd();
        }

        // Set data if result is not null
        if (result !== null) {
          setData(result);
        }
        
        return result;
      } catch (err) {
        clearTimeout(timeoutId);
        
        // Handle specific error types
        const apiError = err as ApiError;
        
        // Detailed error logging for natural language queries
        if (isNaturalLanguageQuery) {
          console.group('❌ Query Error');
          console.error('Error Details:', apiError);
          
          // Safe error type extraction
          const errorType = typeof apiError.detail === 'object' 
            ? (apiError.detail as { error_type?: string }).error_type 
            : undefined;
          
          console.log('Error Type:', errorType);
          console.log('Error Message:', apiError.message);
          console.groupEnd();
        }
        
        // Determine if retry is appropriate based on error type
        const retryableErrors = [
          'database_error', 
          'query_timeout', 
          'unexpected_error', 
          'empty_response',
          'connection_error'
        ];
        
        // Safely extract error type
        const errorType = typeof apiError.detail === 'object' 
          ? (apiError.detail as { error_type?: string }).error_type 
          : undefined;

        const isRetryable = errorType 
          ? retryableErrors.includes(errorType)
          : false;

        if (retries < MAX_RETRIES && isRetryable) {
          // Exponential backoff for retries
          const backoff = INITIAL_BACKOFF * Math.pow(2, retries);
          await new Promise(resolve => setTimeout(resolve, backoff));
          
          retries++;
          
          setProgress({
            current: 0,
            total: 0,
            percentage: 0,
            stage: `Retrying (${retries})`
          });
          
          continue;
        }

        // Final error handling
        setError(apiError);
        setIsLoading(false);
        setProgress({ 
          current: 0, 
          total: 0, 
          percentage: 0,
          stage: 'Error' 
        });
        
        return null;
      }
    }

    // Fallback return
    setIsLoading(false);
    return null;
  }, []);

  return { 
    data, 
    error, 
    isLoading, 
    progress, 
    execute,
    cancelRequest,
    retry
  };
}
