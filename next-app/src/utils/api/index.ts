import { UUID } from './types/types';
import { API } from './endpoints';

// Get base URL from environment or default
const BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 
                 process.env.BACKEND_URL || 
                 'http://localhost:8081';

// Utility function to construct full API URL
export const getApiUrl = (path: string) => `${BASE_URL}${path}`;

// Enhanced fetch function with dynamic base URL
export const apiFetch = async (path: string, options: RequestInit = {}) => {
  const url = getApiUrl(path);
  
  const defaultHeaders = {
    'Content-Type': 'application/json',
  };

  const mergedOptions = {
    ...options,
    headers: {
      ...defaultHeaders,
      ...options.headers,
    },
  };

  try {
    const response = await fetch(url, mergedOptions);
    
    if (!response.ok) {
      throw new Error(`API request failed: ${response.statusText}`);
    }

    return response;
  } catch (error) {
    console.error(`Error fetching ${url}:`, error);
    throw error;
  }
};

export { API };
