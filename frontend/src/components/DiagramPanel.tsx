import React, { useEffect, useRef, useState } from 'react';
import { 
  Box, 
  Paper, 
  Typography, 
  CircularProgress, 
  TextField,
  Divider,
  IconButton,
  Tooltip,
  Button
} from '@mui/material';
import { Code as CodeIcon, BubbleChart as BubbleChartIcon } from '@mui/icons-material'
import mermaid from 'mermaid';
import PlantUMLViewer from './PlantUMLViewer';

interface DiagramPanelProps {
  code?: string;
  loading?: boolean;
  error?: string;
  showCodeEditor?: boolean;
  onCodeChange?: (newCode: string) => void;
  onSyntaxChange?: (syntax: string) => void;
  onTypeChange?: (type: string) => void;
  onToggleCodeEditor?: () => void;
}

const DiagramPanel: React.FC<DiagramPanelProps> = ({
  code,
  loading = false,
  error,
  showCodeEditor = false,
  onCodeChange,
  onToggleCodeEditor,
}) => {
  const diagramRef = useRef<HTMLDivElement>(null);
  const [renderError, setRenderError] = useState<string | null>(null);
  const [editorValue, setEditorValue] = useState<string>('');
  const [currentSyntax, setCurrentSyntax] = useState<string>('mermaid');
  const [currentType, setCurrentType] = useState<string>('auto');

  // Update editor value and detect diagram type when code changes
  useEffect(() => {
    if (code) {
      setEditorValue(code);
      
      // Detect syntax and type from code content
      const lowerCode = code.toLowerCase();
      
      // Detect syntax type
      if (lowerCode.includes('@startuml')) {
        setCurrentSyntax('plantuml');
      } else {
        setCurrentSyntax('mermaid');
      }
      
      // Detect diagram subtype
      if (lowerCode.includes('graph') || lowerCode.includes('flowchart')) {
        setCurrentType('flowchart');
      } else if (lowerCode.includes('sequencediagram')) {
        setCurrentType('sequence');
      } else if (lowerCode.includes('classdiagram')) {
        setCurrentType('class');
      } else if (lowerCode.includes('statediagram')) {
        setCurrentType('state');
      } else if (lowerCode.includes('erdiagram')) {
        setCurrentType('er');
      } else if (lowerCode.includes('gantt')) {
        setCurrentType('gantt');
      } else if (lowerCode.includes('pie')) {
        setCurrentType('pie');
      } else if (lowerCode.includes('mindmap')) {
        setCurrentType('mindmap');
      } else if (lowerCode.includes('timeline')) {
        setCurrentType('timeline');
      } else {
        setCurrentType('auto');
      }
    }
  }, [code]);

  // Render diagram when code changes or when showCodeEditor changes
  useEffect(() => {
    const renderDiagram = async () => {
      // Only skip rendering if we're explicitly showing the code editor
      // This allows the diagram to render on first load and when switching back to diagram view
      if (!diagramRef.current || !code || (showCodeEditor === true)) return;

      try {
        setRenderError(null);
        diagramRef.current.innerHTML = '';

        if (currentSyntax === 'mermaid') {
          await mermaid.initialize({
            startOnLoad: false,
            theme: 'dark',
            securityLevel: 'loose',
          });

          const { svg } = await mermaid.render('diagram', code);
          diagramRef.current.innerHTML = svg;
        }
      } catch (err) {
        console.error('Failed to render diagram:', err);
        setRenderError(err instanceof Error ? err.message : 'Failed to render diagram');
      }
    };

    renderDiagram();
  }, [code, currentSyntax, showCodeEditor]); // Include all dependencies that should trigger a re-render

  const handleCodeChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = event.target.value;
    setEditorValue(newValue);
    if (onCodeChange) {
      onCodeChange(newValue);
    }
  };
  

  return (
    <Paper
      sx={{
        flexGrow: 1,
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
        minHeight: 0,
        p: 2,
        position: 'relative',
      }}
    >
      <Box sx={{ mb: 2, flexShrink: 0, display: 'flex', alignItems: 'center', gap: 2 }}>
        <Button
          variant="outlined"
          size="small"
          startIcon={showCodeEditor ? 
            <BubbleChartIcon /> : 
            <CodeIcon />
          }
          onClick={() => onToggleCodeEditor?.()}
          sx={{ mr: 1 }}
        >
          {showCodeEditor ? "Show Diagram" : "Show Code"}
        </Button>
      </Box>

      <Divider sx={{ mb: 2, flexShrink: 0 }} />
      
      {loading && (
        <Box
          sx={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            backgroundColor: 'rgba(0, 0, 0, 0.7)',
            zIndex: 10,
            gap: 2
          }}
        >
          <CircularProgress size={60} />
          <Typography variant="h6" color="white">
            Generating Diagram...
          </Typography>
          <Typography variant="body2" color="white" sx={{ textAlign: 'center', maxWidth: '80%' }}>
            This may take a few moments while the AI processes your request
          </Typography>
        </Box>
      )}

      {(error || renderError) && (
        <Box sx={{ p: 2, color: 'error.main', flexShrink: 0 }}>
          <Typography variant="body2" color="error">
            {error || renderError}
          </Typography>
        </Box>
      )}

      {showCodeEditor ? (
        <TextField
          multiline
          fullWidth
          variant="outlined" 
          value={editorValue}
          onChange={handleCodeChange}
          placeholder="Edit diagram code here..."
          InputProps={{
            sx: {
              fontFamily: 'monospace',
              fontSize: '0.9rem',
              height: '100%'
            }
          }}
          sx={{
            flexGrow: 1,
            minHeight: 0,
            '& .MuiInputBase-root': {
              height: '100%',
              overflow: 'auto'
            },
            '& .MuiInputBase-input': {
              height: '100%',
              overflow: 'auto !important',
              scrollbarWidth: 'thin',
              '&::-webkit-scrollbar': {
                width: '8px',
              },
              '&::-webkit-scrollbar-thumb': {
                backgroundColor: 'rgba(255, 255, 255, 0.2)',
                borderRadius: '4px',
              }
            }
          }}
        />
      ) : (
        <Box
          sx={{
            flexGrow: 1,
            minHeight: 0,
            overflow: 'auto',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            scrollbarWidth: 'thin',
            '&::-webkit-scrollbar': {
              width: '8px',
              height: '8px'
            },
            '&::-webkit-scrollbar-thumb': {
              backgroundColor: 'rgba(255, 255, 255, 0.2)',
              borderRadius: '4px',
            }
          }}
        >
          {currentSyntax === 'mermaid' ? (
            <Box
              ref={diagramRef}
              sx={{
                width: 'fit-content',
                height: 'fit-content',
                maxWidth: '100%',
                maxHeight: '100%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                padding: 2,
                '& svg': {
                  maxWidth: '100%',
                  maxHeight: '100%',
                },
              }}
            />
          ) : (
            <PlantUMLViewer 
              code={code || ''} 
              onError={(error) => setRenderError(error)}
            />
          )}
        </Box>
      )}
    </Paper>
  );
};

export default DiagramPanel;
