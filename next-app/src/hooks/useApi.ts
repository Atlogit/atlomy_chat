import { useState, useCallback } from 'react';
import { fetchApi } from '../utils/api';

interface ApiHookResult<T> {
  data: T | null;
  error: Error | null;
  isLoading: boolean;
  progress: { current: number; total: number };
  execute: (endpoint: string, options?: RequestInit, timeout?: number) => Promise<T | null>;
}

const DEFAULT_TIMEOUT = 300000; // 5 minutes
const MAX_RETRIES = 0;
const INITIAL_BACKOFF = 1000; // 1 second

export function useApi<T>(): ApiHookResult<T> {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [progress, setProgress] = useState<{ current: number; total: number }>({ current: 0, total: 0 });

  const execute = useCallback(async (endpoint: string, options?: RequestInit, timeout: number = DEFAULT_TIMEOUT): Promise<T | null> => {
    setIsLoading(true);
    setError(null);
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
        setData(result);
        setIsLoading(false);
        return result;
      } catch (err) {
        console.error(`API Error (attempt ${retries + 1}):`, err);
        
        if (retries === MAX_RETRIES) {
          setError(err instanceof Error ? err : new Error('An unknown error occurred'));
          setIsLoading(false);
          return null;
        }

        // Exponential backoff
        const backoff = INITIAL_BACKOFF * Math.pow(2, retries);
        await new Promise(resolve => setTimeout(resolve, backoff));
        
        retries++;
      } finally {
        clearTimeout(timeoutId);
      }
    }

    setIsLoading(false);
    return null;
  }, []);

  return { data, error, isLoading, progress, execute };
}
