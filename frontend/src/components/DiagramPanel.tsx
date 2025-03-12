import React, { useEffect, useRef, useState } from 'react';
import { Box, Paper, Typography, CircularProgress } from '@mui/material';
import mermaid from 'mermaid';

interface DiagramPanelProps {
  code?: string;
  loading?: boolean;
  error?: string;
}

const DiagramPanel: React.FC<DiagramPanelProps> = ({
  code,
  loading = false,
  error,
}) => {
  const diagramRef = useRef<HTMLDivElement>(null);
  const [renderError, setRenderError] = useState<string | null>(null);

  useEffect(() => {
    const renderDiagram = async () => {
      if (!code || !diagramRef.current) return;

      try {
        // Reset error state
        setRenderError(null);

        // Clear previous diagram
        diagramRef.current.innerHTML = '';

        // Initialize mermaid
        await mermaid.initialize({
          startOnLoad: false,
          theme: 'dark',
          securityLevel: 'loose',
        });

        // Render new diagram
        const { svg } = await mermaid.render('diagram', code);
        diagramRef.current.innerHTML = svg;
      } catch (err) {
        console.error('Failed to render diagram:', err);
        setRenderError(err instanceof Error ? err.message : 'Failed to render diagram');
      }
    };

    renderDiagram();
  }, [code]);

  return (
    <Paper
      sx={{
        flexGrow: 1,
        display: 'flex',
        flexDirection: 'column',
        overflow: 'auto',
        p: 2,
        position: 'relative',
      }}
    >
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
          }}
        >
          <CircularProgress />
        </Box>
      )}

      {(error || renderError) && (
        <Box sx={{ p: 2, color: 'error.main' }}>
          <Typography variant="body2" color="error">
            {error || renderError}
          </Typography>
        </Box>
      )}

      <Box
        ref={diagramRef}
        sx={{
          flexGrow: 1,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          '& svg': {
            maxWidth: '100%',
            maxHeight: '100%',
          },
        }}
      />
    </Paper>
  );
};

export default DiagramPanel;
