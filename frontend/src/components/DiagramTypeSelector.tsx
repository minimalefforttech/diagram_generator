import React, { useEffect, useState } from 'react';
import {
  Box,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  SelectChangeEvent,
} from '@mui/material';
import { diagramService } from '../services/api';

interface DiagramTypeSelectorProps {
  currentSyntax: string;
  currentType: string;
  onSyntaxChange: (syntax: string) => void;
  onTypeChange: (type: string) => void;
  disabled?: boolean;
}

const DiagramTypeSelector: React.FC<DiagramTypeSelectorProps> = ({
  currentSyntax,
  currentType,
  onSyntaxChange,
  onTypeChange,
  disabled = false,
}) => {
  const [availableSyntaxTypes, setAvailableSyntaxTypes] = useState<string[]>([]);
  const [availableSubtypes, setAvailableSubtypes] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadSyntaxTypes = async () => {
      try {
        const response = await diagramService.getSyntaxTypes();
        setAvailableSyntaxTypes(response.syntax);
        // Update subtypes when syntax changes
        if (response.types[currentSyntax]) {
          setAvailableSubtypes(response.types[currentSyntax]);
        }
      } catch (error) {
        console.error('Failed to load syntax types:', error);
        // Set defaults in case of error
        setAvailableSyntaxTypes(['mermaid']);
        setAvailableSubtypes(['flowchart', 'sequence', 'class', 'state', 'er']);
      } finally {
        setLoading(false);
      }
    };

    loadSyntaxTypes();
  }, [currentSyntax]);

  const handleSyntaxChange = (event: SelectChangeEvent<string>) => {
    const newSyntax = event.target.value;
    onSyntaxChange(newSyntax);
  };

  const handleTypeChange = (event: SelectChangeEvent<string>) => {
    const newType = event.target.value;
    onTypeChange(newType);
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
      <FormControl size="small" disabled={disabled || loading}>
        <InputLabel id="syntax-type-label">Syntax</InputLabel>
        <Select
          labelId="syntax-type-label"
          value={currentSyntax}
          label="Syntax"
          onChange={handleSyntaxChange}
        >
          {availableSyntaxTypes.map((syntax) => (
            <MenuItem key={syntax} value={syntax}>
              {syntax.charAt(0).toUpperCase() + syntax.slice(1)}
            </MenuItem>
          ))}
        </Select>
      </FormControl>

      <FormControl size="small" disabled={disabled || loading}>
        <InputLabel id="diagram-type-label">Type</InputLabel>
        <Select
          labelId="diagram-type-label"
          value={currentType}
          label="Type"
          onChange={handleTypeChange}
        >
          <MenuItem value="auto">Auto</MenuItem>
          {availableSubtypes.map((type) => (
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