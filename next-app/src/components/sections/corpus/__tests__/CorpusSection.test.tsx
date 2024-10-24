import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { CorpusSection } from '../CorpusSection';

// Mock the imported components
jest.mock('../ListTexts', () => ({
  ListTexts: ({ onTextSelect }: { onTextSelect: (text: string) => void }) => (
    <div data-testid="list-texts">
      List Texts
      <button onClick={() => onTextSelect('sample-text-id')}>Select Text</button>
    </div>
  ),
}));

jest.mock('../SearchForm', () => ({
  SearchForm: ({ onResultSelect }: { onResultSelect: (text: string) => void }) => (
    <div data-testid="search-form">
      Search Form
      <button onClick={() => onResultSelect('search-result-id')}>Select Result</button>
    </div>
  ),
}));

jest.mock('../TextDisplay', () => ({
  TextDisplay: ({ textId }: { textId: string }) => (
    <div data-testid="text-display">Displaying Text: {textId}</div>
  ),
}));

describe('CorpusSection', () => {
  test('renders correctly', () => {
    render(<CorpusSection />);
    expect(screen.getByText('Corpus Manager')).toBeInTheDocument();
    expect(screen.getByText('List Texts')).toBeInTheDocument();
    expect(screen.getByText('Search')).toBeInTheDocument();
  });

  test('displays ListTexts by default', () => {
    render(<CorpusSection />);
    expect(screen.getByTestId('list-texts')).toBeInTheDocument();
  });

  test('changes active view when clicking on tabs', () => {
    render(<CorpusSection />);

    fireEvent.click(screen.getByText('Search'));
    expect(screen.getByTestId('search-form')).toBeInTheDocument();

    fireEvent.click(screen.getByText('List Texts'));
    expect(screen.getByTestId('list-texts')).toBeInTheDocument();
  });

  test('shows View Text tab and displays text when a text is selected from ListTexts', () => {
    render(<CorpusSection />);

    fireEvent.click(screen.getByText('Select Text'));
    expect(screen.getByText('View Text')).toBeInTheDocument();
    expect(screen.getByTestId('text-display')).toBeInTheDocument();
    expect(screen.getByText('Displaying Text: sample-text-id')).toBeInTheDocument();
  });

  test('shows View Text tab and displays text when a result is selected from SearchForm', () => {
    render(<CorpusSection />);

    fireEvent.click(screen.getByText('Search'));
    fireEvent.click(screen.getByText('Select Result'));
    expect(screen.getByText('View Text')).toBeInTheDocument();
    expect(screen.getByTestId('text-display')).toBeInTheDocument();
    expect(screen.getByText('Displaying Text: search-result-id')).toBeInTheDocument();
  });

  test('applies correct CSS classes to active tab', () => {
    render(<CorpusSection />);

    const listTextsTab = screen.getByText('List Texts');
    expect(listTextsTab).toHaveClass('tab-active');

    fireEvent.click(screen.getByText('Search'));
    expect(listTextsTab).not.toHaveClass('tab-active');
    expect(screen.getByText('Search')).toHaveClass('tab-active');
  });
});
