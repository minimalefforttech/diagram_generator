import React, { useEffect, useState, useRef } from 'react';
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
  CircularProgress,
  Switch,
  FormControlLabel,
} from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import { diagramService } from '../services/api';
import ThemeToggle from './ThemeToggle';
import { ModelInfo } from '../types';
// Add webkitdirectory to HTMLInputElement
declare module 'react' {
  interface HTMLAttributes<T> extends AriaAttributes, DOMAttributes<T> {
    webkitdirectory?: string;
    directory?: string;
  }
}

// Component Props
interface ConfigurationScreenProps {
  onStartDiagramGeneration: (config: {
    prompt: string;
    description?: string;
    model: string;
    syntax_type: string;
    subtype?: string;
    options?: {
      rag?: {
        enabled: boolean;
        api_doc_dir: string;
      };
    };
  }) => void;
  onSyntaxChange?: (syntax: string) => void;
  onTypeChange?: (type: string) => void;
}

const USER_PREFERENCES_KEY = 'diagramGeneratorPreferences';

interface UserPreferences {
  model?: string;
  syntax?: string;
  diagramType?: string;
  rag?: {
    enabled: boolean;
    api_doc_dir: string;
  };
}

const ConfigurationScreen: React.FC<ConfigurationScreenProps> = ({
  onStartDiagramGeneration,
  onSyntaxChange,
  onTypeChange
}) => {
  const [prompt, setPrompt] = useState('');
  const [description, setDescription] = useState('');
  const [selectedModel, setSelectedModel] = useState('');
  const [syntax, setSyntax] = useState('mermaid');
  const [diagramType, setDiagramType] = useState('auto');
  const [error, setError] = useState<string | null>(null);
  const [preferences, setPreferences] = useState<UserPreferences>({});
  const [ragEnabled, setRagEnabled] = useState(false);
  const [ragDirectory, setRagDirectory] = useState('');
  // Rest of the component code remains the same...
  // Copy from the previous version starting from modelsQuery definition
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
        
        if (parsedPrefs.syntax) {
          setSyntax(parsedPrefs.syntax);
        }
        if (parsedPrefs.diagramType) {
          setDiagramType(parsedPrefs.diagramType);
        }
        if (parsedPrefs.rag) {
          setRagEnabled(parsedPrefs.rag.enabled);
          setRagDirectory(parsedPrefs.rag.api_doc_dir);
        }
      }
    } catch (error) {
      console.error('Failed to load preferences:', error);
    }
  }, []);

  // Set selected model from preferences after models are loaded
  useEffect(() => {
    if (modelsQuery.isSuccess && modelsQuery.data && preferences.model && !selectedModel) {
      const modelExists = modelsQuery.data.some(model => 
        model.name === preferences.model || model.id === preferences.model
      );
      
      if (modelExists) {
        setSelectedModel(preferences.model);
      }
    }
  }, [modelsQuery.isSuccess, modelsQuery.data, preferences.model, selectedModel]);

  const savePreferences = (prefs: Partial<UserPreferences>) => {
    try {
      const updatedPrefs = { ...preferences, ...prefs };
      setPreferences(updatedPrefs);
      localStorage.setItem(USER_PREFERENCES_KEY, JSON.stringify(updatedPrefs));
    } catch (error) {
      console.error('Failed to save preferences:', error);
    }
  };

  const saveRagPreferences = (enabled: boolean, directory: string) => {
    savePreferences({
      rag: {
        enabled,
        api_doc_dir: directory
      }
    });
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
    if (!prompt.trim()) {
      setError('Please enter a prompt');
      return;
    }
    if (ragEnabled && !ragDirectory.trim()) {
      setError('Please select a references directory');
      return;
    }
    onStartDiagramGeneration({
      prompt: prompt.trim(), // The actual diagram description
      description: description.trim() || undefined, // Optional title
      model: selectedModel,
      syntax_type: syntax,
      subtype: diagramType === 'auto' ? undefined : diagramType,
      options: {
        rag: ragEnabled ? {
          enabled: true,
          api_doc_dir: ragDirectory
        } : undefined
      }
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
              setDiagramType('auto');
              savePreferences({ syntax: newSyntax, diagramType: 'auto' });
              if (onSyntaxChange) {
          onSyntaxChange(newSyntax);
              }
            }}
          >
            {renderSyntaxMenuItems()}
          </Select>
          <FormHelperText>Select the diagram syntax to use</FormHelperText>
        </FormControl>
        
        {syntax.toLowerCase() === 'plantuml' && (
          <Box sx={{ mb: 1 }}>
            <Typography variant="body2" color="warning.main" sx={{ display: 'flex', alignItems: 'center' }}>
              ⚠️ PlantUML may be unreliable with local models. Results may vary.
            </Typography>
          </Box>
        )}

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
              if (onTypeChange) {
                onTypeChange(newType);
              }
            }}
          >
            {renderDiagramTypeMenuItems()}
          </Select>
          <FormHelperText>Select the specific diagram type or let the system detect it</FormHelperText>
        </FormControl>

        <FormControlLabel
          control={
            <Switch
              checked={ragEnabled}
              onChange={(e) => {
                const enabled = e.target.checked;
                setRagEnabled(enabled);
                saveRagPreferences(enabled, ragDirectory);
                if (!enabled) {
                  setError(null);
                }
              }}
              color="primary"
            />
          }
          label="Enable References (RAG)"
        />

        {ragEnabled && (
          <>
            <TextField
              fullWidth
              label="Reference Directory"
              value={ragDirectory}
              onChange={(e) => {
                const directory = e.target.value;
                setRagDirectory(directory);
                saveRagPreferences(ragEnabled, directory);
              }}
              error={ragEnabled && error?.includes('Reference directory')}
              helperText="Enter the full path to a directory containing code files (.py, .ts, .js, etc.) or documentation (.md). This will significantly increase the time taken to generate. This feature is expiremental."
            />
          </>
        )}

        <TextField
          fullWidth
          label="Title (Optional)"
          value={description}
          hidden={true}  // Not currently working
          onChange={(e) => {
            setDescription(e.target.value);
            setError(null);
          }}
          helperText="A short title to identify this diagram in the history panel"
        />

        <TextField
          fullWidth
          multiline
          rows={4}
          label="Diagram Description"
          value={prompt}
          onChange={(e) => {
            setPrompt(e.target.value);
            setError(null);
          }}
          error={!!error && !error.includes('Reference directory')}
          helperText={error || "Describe the diagram you want to create"}
          required
        />

        <Button 
          type="submit"
          variant="contained"
          color="primary"
          size="large"
          disabled={modelsQuery.isLoading || syntaxTypesQuery.isLoading}
          startIcon={modelsQuery.isLoading || syntaxTypesQuery.isLoading ? <CircularProgress size={20} color="inherit" /> : undefined}
        >
          {modelsQuery.isLoading || syntaxTypesQuery.isLoading ? 'Loading Services...' : 'Generate Diagram'}
        </Button>
        
        {(modelsQuery.isLoading || syntaxTypesQuery.isLoading) && (
          <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block', textAlign: 'center' }}>
            Loading required data from the backend...
          </Typography>
        )}
      </Paper>
    </Box>
  );
};

export default ConfigurationScreen;
