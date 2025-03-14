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

  const [syntaxResponse, setSyntaxResponse] = useState<SyntaxTypesResponse | null>(null);

  // Load available syntax types once
  useEffect(() => {
    const loadTypes = async () => {
      try {
        const response = await diagramService.getSyntaxTypes();
        setSyntaxTypes(response.syntax);
        setSyntaxResponse(response);
        setError(null);
      } catch (error) {
        console.error('Failed to load diagram types:', error);
        setError('Failed to load diagram types');
        // Use default values from the API service's error handler
        const defaultTypes = await diagramService.getSyntaxTypes();
        setSyntaxTypes(defaultTypes.syntax);
        setSyntaxResponse(defaultTypes);
      } finally {
        setLoading(false);
      }
    };

    loadTypes();
  }, []);

  // Update subtypes whenever syntax or response changes
  useEffect(() => {
    if (syntaxResponse) {
      const types = syntaxResponse.types[currentSyntax] || [];
      setSubtypes(['auto', ...types]);
    }
  }, [currentSyntax, syntaxResponse]);

  const handleSyntaxChange = (event: any) => {
    const newSyntax = event.target.value;
    onSyntaxChange(newSyntax);
    // Let the parent component handle type reset
    onTypeChange('auto');
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
