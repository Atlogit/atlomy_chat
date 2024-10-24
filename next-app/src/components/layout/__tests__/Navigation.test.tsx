import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { Navigation } from '../Navigation';

describe('Navigation', () => {
  const mockOnTabChange = jest.fn();

  beforeEach(() => {
    mockOnTabChange.mockClear();
  });

  test('renders all tabs', () => {
    render(<Navigation activeTab="llm" onTabChange={mockOnTabChange} />);
    expect(screen.getByText('LLM Assistant')).toBeInTheDocument();
    expect(screen.getByText('Lexical Values')).toBeInTheDocument();
    expect(screen.getByText('Corpus Manager')).toBeInTheDocument();
  });

  test('highlights active tab', () => {
    render(<Navigation activeTab="lexical" onTabChange={mockOnTabChange} />);
    const activeTab = screen.getByText('Lexical Values');
    expect(activeTab.parentElement).toHaveClass('tab-active');
  });

  test('calls onTabChange when a tab is clicked', () => {
    render(<Navigation activeTab="llm" onTabChange={mockOnTabChange} />);
    const corpusTab = screen.getByText('Corpus Manager');
    fireEvent.click(corpusTab);
    expect(mockOnTabChange).toHaveBeenCalledWith('corpus');
  });

  test('renders correct icons for each tab', () => {
    render(<Navigation activeTab="llm" onTabChange={mockOnTabChange} />);
    const tabs = screen.getAllByRole('button');
    expect(tabs).toHaveLength(3);
    tabs.forEach((tab) => {
      expect(tab.querySelector('svg')).toBeInTheDocument();
    });
  });

  test('has correct CSS classes', () => {
    const { container } = render(<Navigation activeTab="llm" onTabChange={mockOnTabChange} />);
    const navigationContainer = container.firstChild;
    expect(navigationContainer).toHaveClass('tabs tabs-boxed justify-center bg-base-100 p-2 rounded-lg shadow-md');
  });
});
