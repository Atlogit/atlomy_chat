import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { LLMSection } from '../LLMSection';

// Mock dependencies
jest.mock('components/ui/Button', () => ({
  Button: ({ children, onClick, disabled, isLoading }: { children: React.ReactNode; onClick: () => void; disabled: boolean; isLoading: boolean }) => (
    <button onClick={onClick} disabled={disabled || isLoading}>{isLoading ? 'Loading...' : children}</button>
  ),
}));

jest.mock('components/ui/ResultsDisplay', () => ({
  ResultsDisplay: ({ content, error }: { content: string | null; error: string | null }) => (
    <div data-testid="results-display">
      {content && <div data-testid="content">{content}</div>}
      {error && <div data-testid="error">{error}</div>}
    </div>
  ),
}));

const mockExecute = jest.fn();
const mockUseLoading = jest.fn();
jest.mock('hooks/useLoading', () => ({
  useLoading: () => mockUseLoading(),
}));

const mockFetchApi = jest.fn();
jest.mock('utils/api', () => ({
  fetchApi: (...args: any[]) => mockFetchApi(...args),
  API: {
    llm: {
      query: '/api/llm/query',
    },
  },
}));

describe('LLMSection', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockUseLoading.mockReturnValue({
      isLoading: false,
      error: null,
      execute: mockExecute,
    });
  });

  test('renders correctly', () => {
    render(<LLMSection />);
    expect(screen.getByText('LLM Assistant')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Ask a question about the texts...')).toBeInTheDocument();
    expect(screen.getByText('Ask Question')).toBeInTheDocument();
  });

  test('handles user input', () => {
    render(<LLMSection />);
    const textarea = screen.getByPlaceholderText('Ask a question about the texts...');
    fireEvent.change(textarea, { target: { value: 'Test query' } });
    expect(textarea).toHaveValue('Test query');
  });

  test('disables submit button when query is empty', () => {
    render(<LLMSection />);
    const submitButton = screen.getByText('Ask Question');
    expect(submitButton).toBeDisabled();

    const textarea = screen.getByPlaceholderText('Ask a question about the texts...');
    fireEvent.change(textarea, { target: { value: 'Test query' } });
    expect(submitButton).not.toBeDisabled();
  });

  test('calls API with correct parameters when submit button is clicked', async () => {
    render(<LLMSection />);
    const textarea = screen.getByPlaceholderText('Ask a question about the texts...');
    const submitButton = screen.getByText('Ask Question');

    fireEvent.change(textarea, { target: { value: 'Test query' } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(mockExecute).toHaveBeenCalledWith(
        expect.any(Promise)
      );
      expect(mockFetchApi).toHaveBeenCalledWith('/api/llm/query', {
        method: 'POST',
        body: JSON.stringify({ query: 'Test query' }),
      });
    });
  });

  test('displays API response correctly', async () => {
    const apiResponse = { answer: 'API response' };
    mockExecute.mockResolvedValue(apiResponse);

    render(<LLMSection />);
    const textarea = screen.getByPlaceholderText('Ask a question about the texts...');
    const submitButton = screen.getByText('Ask Question');

    fireEvent.change(textarea, { target: { value: 'Test query' } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByTestId('content')).toHaveTextContent('Test query');
    });
  });

  test('clears query after successful submission', async () => {
    mockExecute.mockResolvedValue({ success: true });
    render(<LLMSection />);
    const textarea = screen.getByPlaceholderText('Ask a question about the texts...');
    const submitButton = screen.getByText('Ask Question');

    fireEvent.change(textarea, { target: { value: 'Test query' } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(textarea).toHaveValue('');
    });
  });

  test('displays error message when API call fails', async () => {
    const errorMessage = 'API error';
    mockUseLoading.mockReturnValue({
      isLoading: false,
      error: errorMessage,
      execute: mockExecute,
    });
    mockExecute.mockRejectedValue(new Error(errorMessage));

    render(<LLMSection />);
    const textarea = screen.getByPlaceholderText('Ask a question about the texts...');
    const submitButton = screen.getByText('Ask Question');

    fireEvent.change(textarea, { target: { value: 'Test query' } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByTestId('error')).toHaveTextContent(errorMessage);
    });
  });

  test('handles loading state correctly', async () => {
    mockUseLoading.mockReturnValue({
      isLoading: true,
      error: null,
      execute: mockExecute,
    });

    render(<LLMSection />);
    const submitButton = screen.getByText('Loading...');
    expect(submitButton).toBeDisabled();
  });
});
