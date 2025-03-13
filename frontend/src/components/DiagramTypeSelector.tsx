import React, { useEffect, useState } from 'react';
import { Box, FormControl, InputLabel, Select, MenuItem } from '@mui/material';
import { diagramService } from '../services/api';
import { SyntaxTypesResponse } from '../types';

interface DiagramTypeSelectorProps {
  currentSyntax: string;
  currentType: string;
  onSyntaxChange: (syntax: string) => void;
  onTypeChange: (type: string) => void;
}

const DiagramTypeSelector: React.FC<DiagramTypeSelectorProps> = ({
  currentSyntax,
  currentType,
  onSyntaxChange,
  onTypeChange,
}) => {
  const [syntaxTypes, setSyntaxTypes] = useState<string[]>([]);
  const [subtypes, setSubtypes] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadTypes = async () => {
      try {
        const response = await diagramService.getSyntaxTypes();
        setSyntaxTypes(response.syntax);
        updateSubtypes(currentSyntax, response);
        setError(null);
      } catch (error) {
        console.error('Failed to load diagram types:', error);
        setError('Failed to load diagram types');
        // Use default values from the API service's error handler
        const defaultTypes = await diagramService.getSyntaxTypes();
        setSyntaxTypes(defaultTypes.syntax);
        updateSubtypes(currentSyntax, defaultTypes);
      } finally {
        setLoading(false);
      }
    };

    loadTypes();
  }, [currentSyntax]);

  const updateSubtypes = (syntax: string, response: SyntaxTypesResponse) => {
    const types = response.types[syntax] || [];
    setSubtypes(['auto', ...types]);
  };

  const handleSyntaxChange = (event: React.ChangeEvent<{ value: unknown }>) => {
    const newSyntax = event.target.value as string;
    onSyntaxChange(newSyntax);
    onTypeChange('auto'); // Reset type when syntax changes
  };

  if (loading) {
    return null;
  }

  return (
    <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
      <FormControl size="small" sx={{ minWidth: 120 }}>
        <InputLabel>Syntax</InputLabel>
        <Select
          value={currentSyntax}
          label="Syntax"
          onChange={handleSyntaxChange}
        >
          {syntaxTypes.map((type) => (
            <MenuItem key={type} value={type}>
              {type.charAt(0).toUpperCase() + type.slice(1)}
            </MenuItem>
          ))}
        </Select>
      </FormControl>

      <FormControl size="small" sx={{ minWidth: 120 }}>
        <InputLabel>Type</InputLabel>
        <Select
          value={currentType}
          label="Type"
          onChange={(e) => onTypeChange(e.target.value as string)}
        >
          {subtypes.map((type) => (
            <MenuItem key={type} value={type}>
              {type.charAt(0).toUpperCase() + type.slice(1)}
            </MenuItem>
          ))}
        </Select>
      </FormControl>
    </Box>
  );
};

export default DiagramTypeSelector;