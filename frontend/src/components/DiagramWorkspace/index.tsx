import { useState } from 'react';
import { 
  AppBar, Toolbar, Typography, Box, Paper, Divider, 
  Grid, CircularProgress, Alert, useTheme
} from '@mui/material';
import { toast } from 'react-toastify';
import { DiagramGenerationRequest, DiagramGenerationResponse, diagramService } from '../../services/api';
import { DiagramEditor } from './DiagramEditor';
import { DiagramPreview } from './DiagramPreview';
import { DiagramControls } from './DiagramControls';
import { ConversationPanel } from '../ConversationPanel';

export interface DiagramWorkspaceProps {
  initialDiagramType?: 'mermaid' | 'plantuml' | 'c4';
}

export function DiagramWorkspace({ initialDiagramType = 'mermaid' }: DiagramWorkspaceProps) {
  const [description, setDescription] = useState('');
  const [diagram, setDiagram] = useState<DiagramGenerationResponse | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [diagramType, setDiagramType] = useState(initialDiagramType);

  const theme = useTheme();

  const handleSubmit = async () => {
    if (!description.trim()) return;

    setIsGenerating(true);
    setError(null);
    toast.info('Generating diagram...');

    try {
      const request: DiagramGenerationRequest = {
        description,
        diagram_type: diagramType,
        options: {
          agent: {
            enabled: true,
            max_iterations: 3
          }
        }
      };

      try {
        // Try to use the actual API
        const response = await diagramService.generate(request);
        setDiagram(response);
        toast.success('Diagram generated successfully!');
      } catch (apiError) {
        console.error('API Error:', apiError);
        toast.warning('Using fallback mock data due to API error');
        
        // Fallback to mock data if API fails
        const mockResponse: DiagramGenerationResponse = {
          diagram: `graph TD
    A[Start] --> B[Process]
    B --> C[Decision]
    C -->|Yes| D[Action 1]
    C -->|No| E[Action 2]
    D --> F[End]
    E --> F`,
          type: diagramType,
          notes: ['Generated from description (mock)', 'Using fallback data']
        };
        
        setDiagram(mockResponse);
      }
      
      setIsGenerating(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
      setIsGenerating(false);
    }
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
      {/* Header */}
      <AppBar position="static" color="primary">
        <Toolbar>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            Diagram Generator
          </Typography>
        </Toolbar>
      </AppBar>

      {/* Main Content */}
      <Box sx={{ display: 'flex', flexGrow: 1, overflow: 'hidden' }}>
        {/* Left Panel */}
        <Grid container>
          <Grid item xs={12} md={6} sx={{ display: 'flex', flexDirection: 'column', borderRight: `1px solid ${theme.palette.divider}` }}>
            <Paper elevation={0} sx={{ p: 2 }}>
              <DiagramControls
                description={description}
                onDescriptionChange={setDescription}
                diagramType={diagramType}
                onDiagramTypeChange={setDiagramType}
                onGenerate={handleSubmit}
                isGenerating={isGenerating}
              />
            </Paper>
            <Divider />
            <Box sx={{ flexGrow: 1, overflow: 'auto' }}>
              <DiagramEditor
                code={diagram?.diagram || ''}
                type={diagramType}
                className="flex-1"
              />
            </Box>
          </Grid>

          {/* Right Panel */}
          <Grid item xs={12} md={6} sx={{ display: 'flex', flexDirection: 'column' }}>
            <Paper elevation={0} sx={{ flexGrow: 1, overflow: 'auto', p: 2 }}>
              {isGenerating ? (
                <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
                  <CircularProgress />
                </Box>
              ) : (
                <DiagramPreview
                  diagram={diagram?.diagram || ''}
                  type={diagramType}
                  className="flex-1"
                />
              )}
            </Paper>
            {diagram && (
              <Paper elevation={0} sx={{ height: '33%', borderTop: `1px solid ${theme.palette.divider}` }}>
                <ConversationPanel
                  diagramId={diagram.type}
                  className="h-full"
                />
              </Paper>
            )}
          </Grid>
        </Grid>
      </Box>

      {/* Error Display */}
      {error && (
        <Alert 
          severity="error" 
          sx={{ 
            position: 'fixed', 
            bottom: 16, 
            right: 16, 
            maxWidth: 400,
            boxShadow: 3
          }}
        >
          {error}
        </Alert>
      )}
    </Box>
  );
}
