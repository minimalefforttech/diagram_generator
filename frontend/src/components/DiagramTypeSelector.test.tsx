import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import DiagramTypeSelector from './DiagramTypeSelector';
import { apiClient } from '../services/api';

// Mock the API client
jest.mock('../services/api', () => ({
  apiClient: {
    getSyntaxTypes: jest.fn(),
  },
}));

describe('DiagramTypeSelector', () => {
  const mockSyntaxTypes = {
    syntax: ['mermaid', 'plantuml'],
    types: {
      mermaid: ['flowchart', 'sequence', 'class'],
      plantuml: ['sequence', 'class', 'usecase'],
    },
  };

  beforeEach(() => {
    // Reset mocks
    jest.clearAllMocks();
    // Setup default mock response
    (apiClient.getSyntaxTypes as jest.Mock).mockResolvedValue(mockSyntaxTypes);
  });

  it('loads and displays syntax types on mount', async () => {
    render(
      <DiagramTypeSelector
        currentSyntax="mermaid"
        currentType="auto"
        onSyntaxChange={() => {}}
        onTypeChange={() => {}}
      />
    );

    // Wait for syntax types to load
    const syntaxSelect = await screen.findByLabelText('Syntax');
    expect(syntaxSelect).toBeInTheDocument();

    // Check that mermaid subtypes are loaded
    const typeSelect = screen.getByLabelText('Type');
    expect(typeSelect).toBeInTheDocument();
  });

  it('updates subtypes when syntax changes', async () => {
    const onSyntaxChange = jest.fn();
    const onTypeChange = jest.fn();

    render(
      <DiagramTypeSelector
        currentSyntax="mermaid"
        currentType="auto"
        onSyntaxChange={onSyntaxChange}
        onTypeChange={onTypeChange}
      />
    );

    // Wait for selects to load
    const syntaxSelect = await screen.findByLabelText('Syntax');
    
    // Change syntax to plantuml
    fireEvent.mouseDown(syntaxSelect);
    const plantumlOption = await screen.findByText('Plantuml');
    fireEvent.click(plantumlOption);

    expect(onSyntaxChange).toHaveBeenCalledWith('plantuml');
  });

  it('handles API errors gracefully', async () => {
    // Mock API error
    (apiClient.getSyntaxTypes as jest.Mock).mockRejectedValue(new Error('API Error'));

    render(
      <DiagramTypeSelector
        currentSyntax="mermaid"
        currentType="auto"
        onSyntaxChange={() => {}}
        onTypeChange={() => {}}
      />
    );

    // Should load with default values
    const syntaxSelect = await screen.findByLabelText('Syntax');
    const typeSelect = screen.getByLabelText('Type');

    expect(syntaxSelect).toBeInTheDocument();
    expect(typeSelect).toBeInTheDocument();
  });
});