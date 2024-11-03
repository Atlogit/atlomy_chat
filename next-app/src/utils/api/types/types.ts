export type UUID = string;

export interface ApiError {
  message: string;
  status?: number;
  detail?: string;
}
