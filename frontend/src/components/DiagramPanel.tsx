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
  Chip
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
  syntax?: string;
  diagramType?: string;
  currentActivity?: string;
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
  syntax = 'mermaid',
  diagramType = 'auto',
  currentActivity = "Generating Diagram..."
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
    configureMonacoEditor(false);
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

  // Update editor value when code changes
  useEffect(() => {
    if (code) {
      setEditorValue(code);
    }
  }, [code]);

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

  // Render diagram when code changes
  useEffect(() => {
    const renderDiagram = async () => {
      if (!code || showCodeEditor) return;

      try {
        setRenderError(null);

        if (currentSyntax === 'mermaid') {
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
      } catch (err) {
        console.error('Failed to render diagram:', err);
        setRenderError(err instanceof Error ? err.message : 'Failed to render diagram');
      }
    };

    renderDiagram();
  }, [code, currentSyntax, showCodeEditor, theme.palette.mode]);

  const handleEditorChange = (value: string | undefined) => {
    setEditorValue(value || '');
    onCodeChange?.(value || '');
  };

  return (
    <Paper sx={{ height: '100%', display: 'flex', flexDirection: 'column', position: 'relative' }}>
      <Box sx={{ mb: 2, p: 2, flexShrink: 0, display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Button
            variant="outlined"
            size="small"
            startIcon={showCodeEditor ? <BubbleChartIcon /> : <CodeIcon />}
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
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Chip 
              label={`${currentSyntax.charAt(0).toUpperCase() + currentSyntax.slice(1)} Diagram`}
              color="primary"
              size="small"
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
              <MenuItem onClick={handleDownloadClose}>Download as SVG</MenuItem>
              <MenuItem onClick={handleDownloadClose}>Download as PNG</MenuItem>
            </Menu>
          </Box>
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
          <Typography variant="h6" color="white" textAlign="center">
            {currentActivity}
          </Typography>
          {currentActivity !== "Generating Diagram..." && (
            <Typography variant="body2" color="white" sx={{ textAlign: 'center', maxWidth: '80%' }}>
              This may take a few moments while the AI processes your request
            </Typography>
          )}
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
              wordWrap: 'on',
              scrollBeyondLastLine: false,
              automaticLayout: true,
            }}
          />
        </Box>
      ) : (
        <Box
          sx={{
            flexGrow: 1,
            minHeight: 0,
            overflow: 'hidden',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            position: 'relative',
            cursor: isDragging ? 'grabbing' : 'grab'
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
                transform: `scale(${scale}) translate(${position.x}px, ${position.y}px)`,
                transition: isDragging ? 'none' : 'transform 0.1s ease-out'
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
        </Box>
      )}
    </Paper>
  );
};

export default DiagramPanel;
