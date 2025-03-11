import { 
  TextField, Button, FormControl, InputLabel, 
  Select, MenuItem, Typography, Box, 
  CircularProgress, FormHelperText, Paper
} from '@mui/material';
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome';

interface DiagramControlsProps {
  description: string;
  onDescriptionChange: (value: string) => void;
  diagramType: 'mermaid' | 'plantuml' | 'c4';
  onDiagramTypeChange: (type: 'mermaid' | 'plantuml' | 'c4') => void;
  onGenerate: () => void;
  isGenerating: boolean;
}

export function DiagramControls({
  description,
  onDescriptionChange,
  diagramType,
  onDiagramTypeChange,
  onGenerate,
  isGenerating
}: DiagramControlsProps) {
  return (
    <Box sx={{ width: '100%' }}>
      <Typography variant="h6" gutterBottom>
        Create New Diagram
      </Typography>
      
      {/* Diagram Type Selection */}
      <FormControl fullWidth margin="normal" size="small">
        <InputLabel id="diagram-type-label">Diagram Type</InputLabel>
        <Select
          labelId="diagram-type-label"
          id="diagram-type"
          value={diagramType}
          label="Diagram Type"
          onChange={(e) => onDiagramTypeChange(e.target.value as 'mermaid' | 'plantuml' | 'c4')}
        >
          <MenuItem value="mermaid">Mermaid</MenuItem>
          <MenuItem value="plantuml">PlantUML</MenuItem>
          <MenuItem value="c4">C4</MenuItem>
        </Select>
        <FormHelperText>
          {diagramType === 'mermaid' && 'Flowcharts, sequence diagrams, class diagrams, etc.'}
          {diagramType === 'plantuml' && 'UML diagrams with PlantUML syntax'}
          {diagramType === 'c4' && 'Context, Container, Component, and Code diagrams'}
        </FormHelperText>
      </FormControl>

      {/* Description Input */}
      <TextField
        id="description"
        label="Description"
        multiline
        rows={4}
        value={description}
        onChange={(e) => onDescriptionChange(e.target.value)}
        placeholder="Describe the diagram you want to generate..."
        fullWidth
        margin="normal"
        variant="outlined"
        helperText="Describe what you want to visualize and the AI will generate a diagram for you"
      />

      {/* Generate Button */}
      <Button
        variant="contained"
        color="primary"
        fullWidth
        onClick={onGenerate}
        disabled={isGenerating || !description.trim()}
        startIcon={isGenerating ? <CircularProgress size={20} color="inherit" /> : <AutoAwesomeIcon />}
        sx={{ mt: 2 }}
      >
        {isGenerating ? 'Generating...' : 'Generate Diagram'}
      </Button>
    </Box>
  );
}
