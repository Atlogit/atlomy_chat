export type UUID = string;

export interface ApiError {
  message: string;
  status?: number;
  detail?: any; // Can be string or structured error object
  error_type?: string;
}
