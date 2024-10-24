import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { ResultsDisplay, ProgressDisplay } from '../ResultsDisplay';

describe('ResultsDisplay', () => {
  test('renders with content', () => {
    render(<ResultsDisplay content="Test content" />);
    expect(screen.getByText('Results')).toBeInTheDocument();
    expect(screen.getByText('Test content')).toBeInTheDocument();
  });

  test('renders with custom title', () => {
    render(<ResultsDisplay title="Custom Title" content="Test content" />);
    expect(screen.getByText('Custom Title')).toBeInTheDocument();
  });

  test('renders error message', () => {
    render(<ResultsDisplay content={null} error="Error message" />);
    expect(screen.getByText('Error message')).toBeInTheDocument();
    expect(screen.getByText('Error message').classList.contains('text-error')).toBe(true);
  });

  test('does not render when content and error are null', () => {
    const { container } = render(<ResultsDisplay content={null} error={null} />);
    expect(container.firstChild).toBeNull();
  });
});

describe('ProgressDisplay', () => {
  test('renders progress correctly', () => {
    render(<ProgressDisplay current={3} total={10} />);
    expect(screen.getByText('Progress:')).toBeInTheDocument();
    expect(screen.getByText('3/10')).toBeInTheDocument();
    const progressBar = screen.getByRole('progressbar');
    expect(progressBar).toBeInTheDocument();
    expect(progressBar).toHaveAttribute('value', '30');
  });

  test('does not render when total is 0', () => {
    const { container } = render(<ProgressDisplay current={0} total={0} />);
    expect(container.firstChild).toBeNull();
  });
});
