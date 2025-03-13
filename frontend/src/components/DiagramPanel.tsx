import React, { useEffect, useRef, useState } from 'react';
import { 
  Box, 
  Paper, 
  Typography, 
  CircularProgress, 
  Divider,
  Button,
  useTheme,
  Menu,
  MenuItem,
} from '@mui/material';
import { 
  Code as CodeIcon, 
  BubbleChart as BubbleChartIcon,
  Download as DownloadIcon 
} from '@mui/icons-material';
import Editor from "@monaco-editor/react";
import mermaid from 'mermaid';
import PlantUMLViewer from './PlantUMLViewer';
import { configureMonacoEditor } from '../utils/editorConfig';

// Initialize Monaco editor configuration
configureMonacoEditor();

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
  onSyntaxChange,
  onTypeChange,
  onToggleCodeEditor,
}) => {
  const theme = useTheme();
  const diagramRef = useRef<HTMLDivElement>(null);
  const [renderError, setRenderError] = useState<string | null>(null);
  const [editorValue, setEditorValue] = useState<string>('');
  const [currentSyntax, setCurrentSyntax] = useState<string>('mermaid');
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);

  // Simplified editor mount handler - always use light theme
  const handleEditorWillMount = (monaco: any) => {
    monaco.editor.setTheme('mermaidLight');
  };

  // Initialize editor configuration
  useEffect(() => {
    configureMonacoEditor(false); // Always use light theme
  }, []);

  // Update both syntax and type when code changes
  useEffect(() => {
    if (code) {
      setEditorValue(code);
      
      // Detect syntax and type from code content
      const lowerCode = code.toLowerCase();
      
      // Detect syntax type
      const newSyntax = lowerCode.includes('@startuml') ? 'plantuml' : 'mermaid';
      setCurrentSyntax(newSyntax);
      if (onSyntaxChange) {
        onSyntaxChange(newSyntax);
      }
      
      // Detect diagram subtype
      let newType = 'auto';
      if (lowerCode.includes('graph') || lowerCode.includes('flowchart')) {
        newType = 'flowchart';
      } else if (lowerCode.includes('sequencediagram')) {
        newType = 'sequence';
      } else if (lowerCode.includes('classdiagram')) {
        newType = 'class';
      } else if (lowerCode.includes('statediagram')) {
        newType = 'state';
      } else if (lowerCode.includes('erdiagram')) {
        newType = 'er';
      } else if (lowerCode.includes('gantt')) {
        newType = 'gantt';
      } else if (lowerCode.includes('pie')) {
        newType = 'pie';
      } else if (lowerCode.includes('mindmap')) {
        newType = 'mindmap';
      } else if (lowerCode.includes('timeline')) {
        newType = 'timeline';
      }
      
      if (onTypeChange) {
        onTypeChange(newType);
      }
    }
  }, [code, onSyntaxChange, onTypeChange]);

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

  const handleDownloadClick = (event: React.MouseEvent<HTMLButtonElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleDownloadClose = () => {
    setAnchorEl(null);
  };

  const downloadAsPNG = () => {
    if (!diagramRef.current) return;
    const svg = diagramRef.current.querySelector('svg');
    if (!svg) return;

    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    const image = new Image();
    
    const svgData = new XMLSerializer().serializeToString(svg);
    const blob = new Blob([svgData], { type: 'image/svg+xml' });
    const url = URL.createObjectURL(blob);

    image.onload = () => {
      canvas.width = image.width;
      canvas.height = image.height;
      ctx?.drawImage(image, 0, 0);
      
      canvas.toBlob((blob) => {
        if (blob) {
          const url = URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = 'diagram.png';
          a.click();
          URL.revokeObjectURL(url);
        }
      }, 'image/png');
    };
    
    image.src = url;
    handleDownloadClose();
  };

  const downloadAsMarkdown = () => {
    const element = document.createElement('a');
    const content = '\`\`\`' + currentSyntax + '\n' + code + '\n\`\`\`';
    const file = new Blob([content], { type: 'text/markdown' });
    element.href = URL.createObjectURL(file);
    element.download = 'diagram.md';
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
    handleDownloadClose();
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
        bgcolor: theme.palette.mode === 'dark' ? '#1E1E1E' : '#FFFFFF',
      }}
    >
      <Box sx={{ mb: 2, flexShrink: 0, display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 2 }}>
        <Button
          variant="outlined"
          size="small"
          startIcon={showCodeEditor ? 
            <BubbleChartIcon /> : 
            <CodeIcon />
          }
          onClick={() => onToggleCodeEditor?.()}
        >
          {showCodeEditor ? "Show Diagram" : "Show Code"}
        </Button>
        
        {!showCodeEditor && code && (
          <>
            <Button
              variant="outlined"
              size="small"
              startIcon={<DownloadIcon />}
              onClick={handleDownloadClick}
            >
              Download
            </Button>
            <Menu
              anchorEl={anchorEl}
              open={Boolean(anchorEl)}
              onClose={handleDownloadClose}
            >
              <MenuItem onClick={downloadAsPNG}>Download as PNG</MenuItem>
              <MenuItem onClick={downloadAsMarkdown}>Download as Markdown</MenuItem>
            </Menu>
          </>
        )}
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
        <Box sx={{ 
          flexGrow: 1, 
          minHeight: 0,
          bgcolor: '#FFFFFF',
          '& .monaco-editor, & .monaco-editor .margin, & .monaco-editor-background': {
            backgroundColor: '#FFFFFF !important'
          }
        }}>
          <Editor
            height="100%"
            defaultValue={editorValue}
            value={editorValue}
            onChange={(value: string | undefined) => {
              setEditorValue(value || '');
              onCodeChange?.(value || '');
            }}
            language={currentSyntax === 'mermaid' ? 'mermaid' : 'plantuml'}
            beforeMount={handleEditorWillMount}
            theme="mermaidLight"
            options={{
              minimap: { enabled: false },
              fontSize: 14,
              lineNumbers: 'on',
              renderLineHighlight: 'all',
              matchBrackets: 'always',
              autoClosingBrackets: 'always',
              autoClosingQuotes: 'always',
              folding: true,
              foldingHighlight: true,
              scrollBeyondLastLine: false,
              wordWrap: 'on',
              wrappingIndent: 'same',
              automaticLayout: true,
              tabSize: 2,
              guides: {
                bracketPairs: true,
                indentation: true
              },
              scrollbar: {
                vertical: 'auto',
                horizontal: 'auto',
                verticalScrollbarSize: 8,
                horizontalScrollbarSize: 8,
                useShadows: true
              },
              padding: {
                top: 8,
                bottom: 8
              },
              bracketPairColorization: {
                enabled: true
              }
            }}
          />
        </Box>
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
