import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { LexicalSection } from '../LexicalSection';

// Mock the imported form components
jest.mock('../CreateForm', () => ({
  CreateForm: () => <div data-testid="create-form">Create Form</div>,
}));

const mockBatchCreate = jest.fn();
jest.mock('../BatchCreateForm', () => ({
  BatchCreateForm: ({ onBatchCreate }: { onBatchCreate: (count: number) => Promise<void> }) => (
    <div data-testid="batch-create-form">
      Batch Create Form
      <button onClick={() => onBatchCreate(5)}>Start Batch Create</button>
    </div>
  ),
}));

jest.mock('../GetForm', () => ({
  GetForm: () => <div data-testid="get-form">Get Form</div>,
}));

jest.mock('../UpdateForm', () => ({
  UpdateForm: () => <div data-testid="update-form">Update Form</div>,
}));

const mockBatchUpdate = jest.fn();
jest.mock('../BatchUpdateForm', () => ({
  BatchUpdateForm: ({ onBatchUpdate }: { onBatchUpdate: (count: number) => Promise<void> }) => (
    <div data-testid="batch-update-form">
      Batch Update Form
      <button onClick={() => onBatchUpdate(10)}>Start Batch Update</button>
    </div>
  ),
}));

jest.mock('../DeleteForm', () => ({
  DeleteForm: () => <div data-testid="delete-form">Delete Form</div>,
}));

// Mock ProgressDisplay component
jest.mock('components/ui/ResultsDisplay', () => ({
  ProgressDisplay: ({ current, total }: { current: number; total: number }) => (
    <div data-testid="progress-display">
      Progress: {current}/{total}
    </div>
  ),
  ResultsDisplay: ({ content, error }: { content: string | null; error: string | null }) => (
    <div data-testid="results-display">
      {content && <div data-testid="content">{content}</div>}
      {error && <div data-testid="error">{error}</div>}
    </div>
  ),
}));

describe('LexicalSection', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  // ... (previous tests remain unchanged)

  test('performs batch create operation and tracks progress', async () => {
    mockBatchCreate.mockImplementation(async (count) => {
      for (let i = 1; i <= count; i++) {
        await new Promise(resolve => setTimeout(resolve, 10));
        mockBatchCreate.mock.calls[0][1](i, count);
      }
    });

    render(<LexicalSection />);

    fireEvent.click(screen.getByText('Batch Create'));
    fireEvent.click(screen.getByText('Start Batch Create'));

    for (let i = 1; i <= 5; i++) {
      await waitFor(() => {
        expect(screen.getByTestId('progress-display')).toHaveTextContent(`Progress: ${i}/5`);
      });
    }
  });

  test('performs batch update operation and tracks progress', async () => {
    mockBatchUpdate.mockImplementation(async (count) => {
      for (let i = 1; i <= count; i++) {
        await new Promise(resolve => setTimeout(resolve, 10));
        mockBatchUpdate.mock.calls[0][1](i, count);
      }
    });

    render(<LexicalSection />);

    fireEvent.click(screen.getByText('Batch Update'));
    fireEvent.click(screen.getByText('Start Batch Update'));

    for (let i = 1; i <= 10; i++) {
      await waitFor(() => {
        expect(screen.getByTestId('progress-display')).toHaveTextContent(`Progress: ${i}/10`);
      });
    }
  });

  test('handles errors in batch create operation', async () => {
    mockBatchCreate.mockImplementation(async () => {
      throw new Error('Batch create error');
    });

    render(<LexicalSection />);

    fireEvent.click(screen.getByText('Batch Create'));
    fireEvent.click(screen.getByText('Start Batch Create'));

    await waitFor(() => {
      expect(screen.getByTestId('error')).toHaveTextContent('Batch create error');
    });
  });

  test('handles errors in batch update operation', async () => {
    mockBatchUpdate.mockImplementation(async () => {
      throw new Error('Batch update error');
    });

    render(<LexicalSection />);

    fireEvent.click(screen.getByText('Batch Update'));
    fireEvent.click(screen.getByText('Start Batch Update'));

    await waitFor(() => {
      expect(screen.getByTestId('error')).toHaveTextContent('Batch update error');
    });
  });
});
