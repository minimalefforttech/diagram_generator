import { useEffect, useRef, useState } from 'react';
import { Box, Typography, Alert, Paper, Skeleton, Chip, Tooltip, IconButton } from '@mui/material';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import DownloadIcon from '@mui/icons-material/Download';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';
import { toast } from 'react-toastify';
import mermaid from 'mermaid';

interface DiagramPreviewProps {
  diagram: string;
  type: 'mermaid' | 'plantuml' | 'c4';
  className?: string;
}

// Initialize mermaid with default config
mermaid.initialize({
  startOnLoad: true,
  theme: 'default',
  securityLevel: 'loose',
  flowchart: {
    htmlLabels: true,
    curve: 'basis',
  },
});

export function DiagramPreview({ diagram, type, className = '' }: DiagramPreviewProps) {
  const [svg, setSvg] = useState<string>('');
  const [error, setError] = useState<string | null>(null);
  const [isRendering, setIsRendering] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    async function renderDiagram() {
      if (!diagram) {
        setSvg('');
        setError(null);
        return;
      }

      setIsRendering(true);
      try {
        switch (type) {
          case 'mermaid':
            try {
              const { svg: mermaidSvg } = await mermaid.render('diagram-' + Date.now(), diagram);
              setSvg(mermaidSvg);
              setError(null);
            } catch (mermaidError) {
              console.error('Mermaid rendering error:', mermaidError);
              setError(`Mermaid syntax error: ${mermaidError instanceof Error ? mermaidError.message : String(mermaidError)}`);
              setSvg('');
            }
            break;

          case 'plantuml':
            // TODO: Implement PlantUML rendering
            // This might involve calling a PlantUML server
            setError('PlantUML rendering not implemented yet');
            break;

          case 'c4':
            // TODO: Implement C4 rendering
            // This might involve using a specific C4 renderer or converting to Mermaid
            setError('C4 rendering not implemented yet');
            break;

          default:
            setError('Unsupported diagram type');
        }
      } catch (err) {
        console.error('Error rendering diagram:', err);
        setError(err instanceof Error ? err.message : 'Error rendering diagram');
        setSvg('');
      } finally {
        setIsRendering(false);
      }
    }

    renderDiagram();
  }, [diagram, type]);

  const handleCopyDiagram = () => {
    if (diagram) {
      navigator.clipboard.writeText(diagram)
        .then(() => toast.success('Diagram code copied to clipboard'))
        .catch(() => toast.error('Failed to copy diagram code'));
    }
  };

  const handleDownloadSvg = () => {
    if (svg) {
      const blob = new Blob([svg], { type: 'image/svg+xml' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `diagram-${new Date().toISOString().slice(0, 10)}.svg`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      toast.success('SVG downloaded successfully');
    }
  };

  return (
    <Box sx={{ height: '100%', position: 'relative', display: 'flex', flexDirection: 'column' }}>
      {/* Diagram Type Indicator */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="subtitle1">Preview</Typography>
        <Box>
          <Chip 
            label={type.toUpperCase()} 
            size="small" 
            color="primary" 
            variant="outlined"
            sx={{ mr: 1 }}
          />
          {diagram && (
            <>
              <Tooltip title="Copy diagram code">
                <IconButton size="small" onClick={handleCopyDiagram}>
                  <ContentCopyIcon fontSize="small" />
                </IconButton>
              </Tooltip>
              {svg && (
                <Tooltip title="Download SVG">
                  <IconButton size="small" onClick={handleDownloadSvg}>
                    <DownloadIcon fontSize="small" />
                  </IconButton>
                </Tooltip>
              )}
            </>
          )}
        </Box>
      </Box>

      {/* Diagram Content */}
      <Paper 
        elevation={0} 
        sx={{ 
          flexGrow: 1, 
          overflow: 'auto', 
          p: 2, 
          border: '1px solid #e0e0e0',
          borderRadius: 1,
          bgcolor: '#fafafa',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center'
        }}
      >
        {error ? (
          <Alert severity="error" sx={{ width: '100%' }}>
            {error}
          </Alert>
        ) : isRendering ? (
          <Skeleton variant="rectangular" width="100%" height="100%" animation="wave" />
        ) : diagram ? (
          <Box
            ref={containerRef}
            sx={{ 
              width: '100%', 
              height: '100%', 
              overflow: 'auto',
              display: 'flex',
              justifyContent: 'center',
              '& svg': {
                maxWidth: '100%',
                height: 'auto'
              }
            }}
            dangerouslySetInnerHTML={{ __html: svg }}
          />
        ) : (
          <Box sx={{ 
            display: 'flex', 
            flexDirection: 'column',
            alignItems: 'center', 
            justifyContent: 'center', 
            color: 'text.secondary',
            p: 4
          }}>
            <InfoOutlinedIcon sx={{ fontSize: 40, mb: 2, opacity: 0.5 }} />
            <Typography variant="body1" align="center">
              Enter a description and click "Generate Diagram" to create a visualization
            </Typography>
          </Box>
        )}
      </Paper>
    </Box>
  );
}
