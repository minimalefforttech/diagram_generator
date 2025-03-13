import React, { useEffect, useState } from 'react';
import {
  Box,
  TextField,
  Button,
  Typography,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Paper,
  FormHelperText,
  CircularProgress
} from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import { diagramService } from '../services/api';
import ThemeToggle from './ThemeToggle';
import { ModelInfo } from '../types';

interface ConfigurationScreenProps {
  onStartDiagramGeneration: (config: {
    description: string;
    model: string;
    syntax: string;
    diagramType?: string;
  }) => void;
}

const USER_PREFERENCES_KEY = 'diagramGeneratorPreferences';

// Define the preferences structure
interface UserPreferences {
  model?: string;
  syntax?: string;
  diagramType?: string;
}

const ConfigurationScreen: React.FC<ConfigurationScreenProps> = ({
  onStartDiagramGeneration
}) => {
  const [description, setDescription] = useState('');
  const [selectedModel, setSelectedModel] = useState('');
  const [syntax, setSyntax] = useState('mermaid');
  const [diagramType, setDiagramType] = useState('auto');
  const [error, setError] = useState<string | null>(null);
  const [preferences, setPreferences] = useState<UserPreferences>({});

  const modelsQuery = useQuery<ModelInfo[]>({
    queryKey: ['models'],
    queryFn: () => diagramService.getAvailableModels("ollama")
  });

  const syntaxTypesQuery = useQuery({
    queryKey: ['syntaxTypes'],
    queryFn: () => diagramService.getSyntaxTypes()
  });

  // Load preferences on component mount
  useEffect(() => {
    try {
      const savedPrefs = localStorage.getItem(USER_PREFERENCES_KEY);
      if (savedPrefs) {
        const parsedPrefs = JSON.parse(savedPrefs) as UserPreferences;
        setPreferences(parsedPrefs);
        
        // Only set syntax and diagram type immediately
        if (parsedPrefs.syntax) {
          setSyntax(parsedPrefs.syntax);
        }
        if (parsedPrefs.diagramType) {
          setDiagramType(parsedPrefs.diagramType);
        }
        // Model will be set after models are loaded
      }
    } catch (error) {
      console.error('Failed to load preferences:', error);
    }
  }, []);

  // Set selected model from preferences after models are loaded
  useEffect(() => {
    if (modelsQuery.isSuccess && modelsQuery.data && preferences.model && !selectedModel) {
      // Check if the saved model is still available
      const modelExists = modelsQuery.data.some(model => 
        model.name === preferences.model || model.id === preferences.model
      );
      
      if (modelExists) {
        setSelectedModel(preferences.model);
      }
    }
  }, [modelsQuery.isSuccess, modelsQuery.data, preferences.model, selectedModel]);

  // Save preferences when they change
  const savePreferences = (prefs: Partial<UserPreferences>) => {
    try {
      const updatedPrefs = { ...preferences, ...prefs };
      setPreferences(updatedPrefs);
      localStorage.setItem(USER_PREFERENCES_KEY, JSON.stringify(updatedPrefs));
    } catch (error) {
      console.error('Failed to save preferences:', error);
    }
  };

  // Reset diagram type when syntax changes
  useEffect(() => {
    setDiagramType('auto');
  }, [syntax]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedModel) {
      setError('Please select a model');
      return;
    }
    if (!description.trim()) {
      setError('Please enter a description');
      return;
    }
    onStartDiagramGeneration({
      description,
      model: selectedModel,
      syntax,
      diagramType: diagramType === 'auto' ? undefined : diagramType
    });
  };

  const renderModelMenuItems = () => {
    if (modelsQuery.isLoading) {
      return (
        <MenuItem disabled>
          <CircularProgress size={20} sx={{ mr: 1 }} />
          Loading models...
        </MenuItem>
      );
    } else if (modelsQuery.isError) {
      return <MenuItem disabled>Error loading models</MenuItem>;
    } else if (!modelsQuery.data || modelsQuery.data.length === 0) {
      return <MenuItem disabled>No models available</MenuItem>;
    } else {
      return modelsQuery.data.map((model) => (
        <MenuItem key={model.id} value={model.name}>
          {model.name}
        </MenuItem>
      ));
    }
  };

  const renderSyntaxMenuItems = () => {
    if (syntaxTypesQuery.isLoading) {
      return <MenuItem disabled>Loading syntax types...</MenuItem>;
    } else if (syntaxTypesQuery.isError) {
      return <MenuItem disabled>Error loading syntax types</MenuItem>;
    } else if (!syntaxTypesQuery.data?.types || Object.keys(syntaxTypesQuery.data.types).length === 0) {
      return <MenuItem disabled>No syntax types available</MenuItem>;
    } else {
      return Object.keys(syntaxTypesQuery.data.types).map((type: string) => (
        <MenuItem key={type} value={type}>
          {type.charAt(0).toUpperCase() + type.slice(1)}
        </MenuItem>
      ));
    }
  };

  const renderDiagramTypeMenuItems = () => {
    const types = syntaxTypesQuery.data?.types?.[syntax] || [];
    return [
      <MenuItem key="auto" value="auto">Auto-detect</MenuItem>,
      ...types.map((type: string) => (
        <MenuItem key={type} value={type}>
          {type.charAt(0).toUpperCase() + type.slice(1)}
        </MenuItem>
      ))
    ];
  };

  return (
    <Box sx={{ 
      height: '100%',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      bgcolor: 'background.default',
      p: 3,
      position: 'relative'
    }}>
      <Box sx={{ position: 'absolute', top: 16, right: 16 }}>
        <ThemeToggle />
      </Box>

      <Paper 
        component="form"
        onSubmit={handleSubmit}
        elevation={3}
        sx={{
          p: 4,
          width: '100%',
          maxWidth: 600,
          display: 'flex',
          flexDirection: 'column',
          gap: 3
        }}
      >
        <Typography variant="h5" component="h1" gutterBottom>
          Create New Diagram
        </Typography>

        <FormControl fullWidth>
          <InputLabel id="model-label">Model</InputLabel>
          <Select
            labelId="model-label"
            value={selectedModel}
            label="Model"
            onChange={(e) => {
              const model = e.target.value;
              setSelectedModel(model);
              savePreferences({ model });
              setError(null);
            }}
          >
            {renderModelMenuItems()}
          </Select>
          <FormHelperText>Select the LLM model to use</FormHelperText>
        </FormControl>

        <FormControl fullWidth>
          <InputLabel id="syntax-label">Syntax</InputLabel>
          <Select
            labelId="syntax-label"
            value={syntax}
            label="Syntax"
            onChange={(e) => {
              const newSyntax = e.target.value;
              setSyntax(newSyntax);
              savePreferences({ syntax: newSyntax });
            }}
          >
            {renderSyntaxMenuItems()}
          </Select>
          <FormHelperText>Select the diagram syntax to use</FormHelperText>
        </FormControl>

        <FormControl fullWidth>
          <InputLabel id="type-label">Diagram Type</InputLabel>
          <Select
            labelId="type-label"
            value={diagramType}
            label="Diagram Type"
            onChange={(e) => {
              const newType = e.target.value;
              setDiagramType(newType);
              savePreferences({ diagramType: newType });
            }}
          >
            {renderDiagramTypeMenuItems()}
          </Select>
          <FormHelperText>Select the specific diagram type or let the system detect it</FormHelperText>
        </FormControl>

        <TextField
          fullWidth
          multiline
          rows={4}
          label="Diagram Description"
          value={description}
          onChange={(e) => {
            setDescription(e.target.value);
            setError(null);
          }}
          error={!!error}
          helperText={error || "Describe the diagram you want to create"}
        />

        <Button 
          type="submit"
          variant="contained"
          color="primary"
          size="large"
          disabled={modelsQuery.isLoading}
        >
          Generate Diagram
        </Button>
      </Paper>
    </Box>
  );
};

export default ConfigurationScreen;