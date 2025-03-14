import React, { useEffect, useRef, useState } from 'react';
import { 
  Box, 
  Paper, 
  Typography, 
  CircularProgress, 
  Button,
  useTheme,
  Menu,
  MenuItem,
  IconButton,
  Chip,
} from '@mui/material';
import { 
  Code as CodeIcon, 
  BubbleChart as BubbleChartIcon,
  Download as DownloadIcon,
  ZoomIn as ZoomInIcon,
  ZoomOut as ZoomOutIcon,
  RestartAlt as ResetIcon
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
  syntax?: string; // Added prop for syntax passed from ConfigurationScreen
  diagramType?: string; // Added prop for diagram type passed from ConfigurationScreen
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
  syntax = 'mermaid', // Default to mermaid if not specified
  diagramType = 'auto', // Default to auto-detect if not specified
}) => {
  const theme = useTheme();
  const diagramRef = useRef<HTMLDivElement>(null);
  const [renderError, setRenderError] = useState<string | null>(null);
  const [editorValue, setEditorValue] = useState<string>('');
  const [currentSyntax, setCurrentSyntax] = useState<string>(syntax);
  const [currentDiagramType, setCurrentDiagramType] = useState<string>(diagramType);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [scale, setScale] = useState(1);
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });

  // Initialize editor configuration
  useEffect(() => {
    configureMonacoEditor(false); // Always use light theme
  }, []);

  // Update syntax from props
  useEffect(() => {
    if (syntax && syntax !== currentSyntax) {
      setCurrentSyntax(syntax);
    }
  }, [syntax]);

  // Update diagram type from props
  useEffect(() => {
    if (diagramType && diagramType !== 'auto') {
      setCurrentDiagramType(diagramType);
    }
  }, [diagramType]);

  // Update both syntax and type when code changes, but only if auto-detect is enabled
  useEffect(() => {
    if (code) {
      setEditorValue(code);
      
      if (diagramType === 'auto') {
        // Detect syntax and type from code content
        const lowerCode = code.toLowerCase();
        
        // Detect syntax type - PlantUML starts with @start*, Mermaid doesn't
        const newSyntax = lowerCode.includes('@start') ? 'plantuml' : 'mermaid';
        setCurrentSyntax(newSyntax);
        if (onSyntaxChange) {
          onSyntaxChange(newSyntax);
        }
        
        // Detect diagram subtype
        let newType = 'auto';
        
        // Mermaid-specific types
        if (newSyntax === 'mermaid') {
          if (lowerCode.includes('gantt')) {
            newType = 'gantt';
          } else if (lowerCode.includes('graph') || lowerCode.includes('flowchart')) {
            newType = 'flowchart';
          } else if (lowerCode.includes('sequencediagram')) {
            newType = 'sequence';
          } else if (lowerCode.includes('classdiagram')) {
            newType = 'class';
          } else if (lowerCode.includes('statediagram')) {
            newType = 'state';
          } else if (lowerCode.includes('erdiagram')) {
            newType = 'er';
          } else if (lowerCode.includes('pie')) {
            newType = 'pie';
          } else if (lowerCode.includes('mindmap')) {
            newType = 'mindmap';
          } else if (lowerCode.includes('timeline')) {
            newType = 'timeline';
          }
        } 
        // PlantUML-specific types
        else {
          if (lowerCode.includes('@startgantt')) {
            newType = 'gantt';
          } else if (lowerCode.includes('@startmindmap')) {
            newType = 'mindmap';
          } else if (lowerCode.includes('@startuml')) {
            newType = 'uml';
          } else if (lowerCode.includes('@startwbs')) {
            newType = 'wbs';
          } else if (lowerCode.includes('@startjson')) {
            newType = 'json';
          }
        }
        
        setCurrentDiagramType(newType);
        if (onTypeChange) {
          onTypeChange(newType);
        }
      }
    }
  }, [code, onSyntaxChange, onTypeChange, diagramType]);

  // Render diagram when code changes or when showCodeEditor changes
  useEffect(() => {
    const renderDiagram = async () => {
      if (!code || showCodeEditor) return;

      try {
        setRenderError(null);

        if (currentSyntax === 'mermaid') {
          // Initialize Mermaid with dynamic config
          await mermaid.initialize({
            startOnLoad: false,
            theme: theme.palette.mode === 'dark' ? 'dark' : 'default',
            securityLevel: 'loose',
          });

          const { svg } = await mermaid.render('diagram', code);
          if (diagramRef.current) {
            diagramRef.current.innerHTML = svg;
          }
        }
        // PlantUML rendering is handled by PlantUMLViewer component
      } catch (err) {
        console.error('Failed to render diagram:', err);
        setRenderError(err instanceof Error ? err.message : 'Failed to render diagram');
      }
    };

    renderDiagram();
  }, [code, currentSyntax, showCodeEditor, theme.palette.mode]);

  // ... existing functions (handleDownloadClick, handleMouseDown, etc.) ...
  const handleDownloadClick = (event: React.MouseEvent<HTMLButtonElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleDownloadClose = () => {
    setAnchorEl(null);
  };

  const handleMouseDown = (e: React.MouseEvent) => {
    if (e.button === 0) { // Left click only
      setIsDragging(true);
      setDragStart({ x: e.clientX - position.x, y: e.clientY - position.y });
    }
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (isDragging) {
      setPosition({
        x: e.clientX - dragStart.x,
        y: e.clientY - dragStart.y
      });
    }
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  const handleWheel = (e: React.WheelEvent) => {
    e.preventDefault();
    const delta = -e.deltaY;
    const scaleFactor = 0.1;
    const newScale = scale + (delta > 0 ? scaleFactor : -scaleFactor);
    
    // Limit scale between 0.1 and 3
    setScale(Math.min(Math.max(0.1, newScale), 3));
  };

  const resetView = () => {
    setScale(1);
    setPosition({ x: 0, y: 0 });
  };

  const zoomIn = () => {
    setScale(Math.min(scale + 0.1, 3));
  };

  const zoomOut = () => {
    setScale(Math.max(scale - 0.1, 0.1));
  };

  const downloadAsSVG = () => {
    // Handle Mermaid diagrams directly from the DOM
    if (currentSyntax === 'mermaid' && diagramRef.current) {
      const svg = diagramRef.current.querySelector('svg');
      if (!svg) return;
      
      // Create a clean SVG with proper XML namespaces
      const svgData = new XMLSerializer().serializeToString(svg);
      const svgBlob = new Blob([svgData], { type: 'image/svg+xml;charset=utf-8' });
      const url = URL.createObjectURL(svgBlob);
      
      // Create download link
      const a = document.createElement('a');
      a.href = url;
      a.download = `diagram-${currentSyntax}.svg`;
      a.click();
      
      // Clean up
      URL.revokeObjectURL(url);
    } 
    // For PlantUML, get the SVG directly from the server
    else if (currentSyntax === 'plantuml' && code) {
      try {
        const plantumlEncoder = require('plantuml-encoder');
        const encodedCode = plantumlEncoder.encode(code);
        
        // Use public PlantUML server or configured server URL from environment
        const serverUrl = process.env.REACT_APP_PLANTUML_SERVER || 'https://www.plantuml.com/plantuml';
        const svgUrl = `${serverUrl}/svg/${encodedCode}`;
        
        // Create download link
        const a = document.createElement('a');
        a.href = svgUrl;
        a.download = `diagram-${currentSyntax}.svg`;
        a.click();
      } catch (err) {
        console.error('Error downloading PlantUML SVG:', err);
      }
    }
    
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

  const handleEditorChange = (value: string | undefined) => {
    setEditorValue(value || '');
    onCodeChange?.(value || '');
  };

  // Get a user-friendly diagram type name
  const getDiagramTypeName = (): string => {
    if (currentDiagramType === 'auto' || !currentDiagramType) {
      // If auto or not set, infer from code content
      if (code?.toLowerCase().includes('gantt')) return 'Gantt';
      if (code?.toLowerCase().includes('mindmap')) return 'MindMap';
      if (code?.toLowerCase().includes('flowchart') || code?.toLowerCase().includes('graph')) return 'Flowchart';
      if (code?.toLowerCase().includes('sequencediagram')) return 'Sequence';
      if (code?.toLowerCase().includes('classdiagram')) return 'Class';
      if (code?.toLowerCase().includes('@startgantt')) return 'Gantt';
      if (code?.toLowerCase().includes('@startmindmap')) return 'MindMap';
      if (code?.toLowerCase().includes('@startuml')) return 'UML';
      if (code?.toLowerCase().includes('@startwbs')) return 'WBS';
      return 'Diagram';
    }
    
    // Use the explicitly set diagram type
    return currentDiagramType.charAt(0).toUpperCase() + currentDiagramType.slice(1);
  };

  return (
    <Paper sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Box sx={{ mb: 2, flexShrink: 0, display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
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
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <IconButton size="small" onClick={zoomOut} title="Zoom out">
                <ZoomOutIcon />
              </IconButton>
              <IconButton size="small" onClick={resetView} title="Reset view">
                <ResetIcon />
              </IconButton>
              <IconButton size="small" onClick={zoomIn} title="Zoom in">
                <ZoomInIcon />
              </IconButton>
            </Box>
          )}
        </Box>
        
        {!showCodeEditor && code && (
          <>
            <Chip 
              label={`Rendering with: ${currentSyntax === 'mermaid' ? 'Mermaid Viewer' : 'PlantUML Viewer'}`}
              color={currentSyntax === 'mermaid' ? 'primary' : 'secondary'}
              size="small"
              sx={{ mx: 'auto' }}
            />
            
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
              <MenuItem onClick={downloadAsSVG}>Download as SVG</MenuItem>
              <MenuItem onClick={downloadAsMarkdown}>Download as Markdown</MenuItem>
            </Menu>
          </>
        )}
      </Box>

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

      {(error || renderError) && !loading && (
        <Box sx={{ p: 2, color: 'error.main', flexShrink: 0 }}>
          <Typography variant="body2" color="error">
            {error || renderError}
          </Typography>
        </Box>
      )}

      {showCodeEditor ? (
        <Box sx={{ flexGrow: 1, minHeight: 0, overflow: 'hidden' }}>
          <Editor
            height="100%"
            defaultLanguage={currentSyntax === 'mermaid' ? 'mermaid' : 'plantuml'}
            value={editorValue}
            onChange={handleEditorChange}
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
        <>
          <Box 
            sx={{ 
              mb: 1, 
              px: 2, 
              display: 'flex', 
              justifyContent: 'space-between',
              alignItems: 'center'
            }}
          >
            <Typography variant="body2" color="textSecondary">
              <strong>Diagram Type:</strong> {`${currentSyntax.charAt(0).toUpperCase() + currentSyntax.slice(1)} (${getDiagramTypeName()})`}
            </Typography>
            
            <Typography variant="caption" color="textSecondary">
              Scale: {Math.round(scale * 100)}%
            </Typography>
          </Box>
          
          <Box
            sx={{
              flexGrow: 1,
              minHeight: 0,
              overflow: 'hidden',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              position: 'relative',
              cursor: isDragging ? 'grabbing' : 'grab',
            }}
            onMouseDown={handleMouseDown}
            onMouseMove={handleMouseMove}
            onMouseUp={handleMouseUp}
            onMouseLeave={handleMouseUp}
            onWheel={handleWheel}
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
                  transform: `scale(${scale}) translate(${position.x}px, ${position.y}px)`,
                  transition: isDragging ? 'none' : 'transform 0.1s ease-out',
                  '& svg': {
                    maxWidth: '100%',
                    maxHeight: '100%',
                  },
                }}
              />
            ) : currentSyntax === 'plantuml' ? (
              <PlantUMLViewer 
                code={code}
                onError={setRenderError}
                scale={scale}
                position={position}
              />
            ) : null}
            {renderError && (
              <Typography color="error" sx={{ position: 'absolute', bottom: 8, left: 8 }}>
                {renderError}
              </Typography>
            )}
          </Box>
        </>
      )}
    </Paper>
  );
};

export default DiagramPanel;
