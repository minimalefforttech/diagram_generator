import React, { useState, useEffect } from 'react';
import {
  Box,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Typography,
  SelectChangeEvent,
  CircularProgress,
} from '@mui/material';
import { diagramService } from '../services/api';
import type { ModelInfo } from '../services/api';

interface ModelSelectorProps {
  selectedModel: string;
  onModelChange: (model: string) => void;
  service?: string;
}

const ModelSelector: React.FC<ModelSelectorProps> = ({
  selectedModel,
  onModelChange,
  service = 'ollama'
}) => {
  const [availableModels, setAvailableModels] = useState<ModelInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch models when the service changes
  useEffect(() => {
    const fetchModels = async () => {
      setLoading(true);
      setError(null);
      
      try {
        const models = await diagramService.getAvailableModels(service);
        setAvailableModels(models);
      } catch (error) {
        setError(`Failed to load models from ${service}`);
        console.error(`Failed to load models from ${service}:`, error);
      } finally {
        setLoading(false);
      }
    };

    fetchModels();
  }, [service]);

  // Separate effect for model selection
  useEffect(() => {
    if (!selectedModel && availableModels.length > 0) {
      onModelChange(availableModels[0].id);
    }
  }, [selectedModel, availableModels, onModelChange]);

  const handleModelChange = (event: SelectChangeEvent<string>) => {
    onModelChange(event.target.value);
  };

  // Format model name for display
  const formatModelName = (model: ModelInfo): string => {
    const parts = model.name.split(':');
    const baseName = parts[0];
    const tag = parts.length > 1 ? parts[1] : 'latest';
    return `${baseName} (${tag})`;
  };

  // Loading state
  if (loading) {
    return (
      <Box sx={{ mt: 2 }}>
        <FormControl fullWidth size="small">
          <InputLabel>Model</InputLabel>
          <Select value="" label="Model" disabled>
            <MenuItem value="">
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <CircularProgress size={16} sx={{ mr: 1 }} />
                <Typography>Loading models...</Typography>
              </Box>
            </MenuItem>
          </Select>
        </FormControl>
      </Box>
    );
  }

  // Error state
  if (error) {
    return (
      <Box sx={{ mt: 2 }}>
        <FormControl fullWidth size="small" error>
          <InputLabel>Model</InputLabel>
          <Select
            value={selectedModel || ''}
            label="Model"
            onChange={handleModelChange}
          >
            <MenuItem value="llama3:latest">
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Typography>Default Model</Typography>
              </Box>
            </MenuItem>
          </Select>
        </FormControl>
        <Typography color="error" variant="caption" sx={{ mt: 0.5, display: 'block' }}>
          {error}
        </Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ mt: 2 }}>
      <FormControl fullWidth size="small">
        <InputLabel id="model-select-label">Model</InputLabel>
        <Select
          labelId="model-select-label"
          id="model-select"
          value={selectedModel}
          label="Model"
          onChange={handleModelChange}
        >
          {availableModels.map((model) => (
            <MenuItem key={model.id} value={model.id}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Typography>{formatModelName(model)}</Typography>
              </Box>
            </MenuItem>
          ))}
        </Select>
      </FormControl>
    </Box>
  );
};

export default ModelSelector;
