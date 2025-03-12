import React, { useEffect, useRef, useState } from 'react';
import { 
  Box, 
  Paper, 
  Typography, 
  CircularProgress, 
  TextField,
  Divider
} from '@mui/material';
import mermaid from 'mermaid';
import DiagramTypeSelector from './DiagramTypeSelector';
import PlantUMLViewer from './PlantUMLViewer';

interface DiagramPanelProps {
  code?: string;
  loading?: boolean;
  error?: string;
  showCodeEditor?: boolean;
  onCodeChange?: (newCode: string) => void;
  onSyntaxChange?: (syntax: string) => void;
  onTypeChange?: (type: string) => void;
}

const DiagramPanel: React.FC<DiagramPanelProps> = ({
  code,
  loading = false,
  error,
  showCodeEditor = false,
  onCodeChange,
  onSyntaxChange,
  onTypeChange
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

  // Render diagram when code changes or editor mode toggles
  useEffect(() => {
    const renderDiagram = async () => {
      if (!code || !diagramRef.current || showCodeEditor) return;

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
  }, [code, showCodeEditor, currentSyntax]);

  const handleCodeChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = event.target.value;
    setEditorValue(newValue);
    if (onCodeChange) {
      onCodeChange(newValue);
    }
  };
  
  const handleSyntaxChange = (syntax: string) => {
    const normalizedSyntax = syntax.toLowerCase();
    if (normalizedSyntax !== currentSyntax) {
      setCurrentSyntax(normalizedSyntax);
      if (onSyntaxChange) {
        onSyntaxChange(normalizedSyntax);
      }
    }
  };
  
  const handleTypeChange = (type: string) => {
    const normalizedType = type.toLowerCase();
    if (normalizedType !== currentType) {
      setCurrentType(normalizedType);
      if (onTypeChange) {
        onTypeChange(normalizedType);
      }
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
      <Box sx={{ mb: 2, flexShrink: 0 }}>
        <DiagramTypeSelector
          currentSyntax={currentSyntax}
          currentType={currentType}
          onSyntaxChange={handleSyntaxChange}
          onTypeChange={handleTypeChange}
          disabled={loading}
        />
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
            alignItems: 'center',
            justifyContent: 'center',
            backgroundColor: 'rgba(0, 0, 0, 0.5)',
            zIndex: 10,
          }}
        >
          <CircularProgress />
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
              height: '100%'
            },
            '& .MuiInputBase-input': {
              height: '100%',
              overflow: 'auto'
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
          }}
        >
          {currentSyntax === 'mermaid' ? (
            <Box
              ref={diagramRef}
              sx={{
                width: '100%',
                height: '100%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
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
