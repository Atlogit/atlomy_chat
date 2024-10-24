import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { Header } from '../Header';

// Mock the Navigation component
jest.mock('../Navigation', () => ({
  Navigation: jest.fn(() => <div data-testid="mock-navigation" />),
}));

describe('Header', () => {
  const mockProps = {
    activeTab: 'test-tab',
    onTabChange: jest.fn(),
  };

  test('renders correctly', () => {
    render(<Header {...mockProps} />);
    expect(screen.getByText('Ancient Medical Texts Analysis')).toBeInTheDocument();
    expect(screen.getByTestId('mock-navigation')).toBeInTheDocument();
  });

  test('passes correct props to Navigation', () => {
    render(<Header {...mockProps} />);
    const { Navigation } = require('../Navigation');
    expect(Navigation).toHaveBeenCalledWith(
      expect.objectContaining(mockProps),
      expect.anything()
    );
  });

  test('has correct CSS classes', () => {
    const { container } = render(<Header {...mockProps} />);
    const header = container.firstChild;
    expect(header).toHaveClass('text-center mb-8 animate-fade-in');
    expect(header?.firstChild).toHaveClass('text-4xl font-bold mb-6 text-primary');
  });
});
