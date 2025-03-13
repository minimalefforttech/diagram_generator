import React, { useState, useEffect } from 'react';
import { Box, Typography, CircularProgress } from '@mui/material';

interface PlantUMLViewerProps {
  code: string;
  onError?: (error: string) => void;
  scale?: number;
  position?: { x: number; y: number };
}

const PlantUMLViewer: React.FC<PlantUMLViewerProps> = ({ 
  code, 
  onError,
  scale = 1,
  position = { x: 0, y: 0 }
}) => {
  const [loading, setLoading] = useState(false);
  const [svgContent, setSvgContent] = useState<string>('');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const renderPlantUML = async () => {
      if (!code) return;

      try {
        setLoading(true);
        setError(null);

        // First compress the PlantUML code using deflate
        const plantumlEncoder = require('plantuml-encoder');
        const encodedCode = plantumlEncoder.encode(code);
        
        // Use public PlantUML server or configured server URL from environment
        const serverUrl = process.env.REACT_APP_PLANTUML_SERVER || 'https://www.plantuml.com/plantuml';
        const response = await fetch(`${serverUrl}/svg/${encodedCode}`);
        
        if (!response.ok) {
          throw new Error('Failed to render PlantUML diagram');
        }

        const svg = await response.text();
        setSvgContent(svg);
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to render diagram';
        setError(errorMessage);
        if (onError) {
          onError(errorMessage);
        }
      } finally {
        setLoading(false);
      }
    };

    renderPlantUML();
  }, [code, onError]);

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', p: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ p: 2, color: 'error.main' }}>
        <Typography variant="body2" component="pre" sx={{ 
          whiteSpace: 'pre-wrap',
          fontFamily: 'monospace',
          fontSize: '0.9rem',
          mt: 2
        }}>
          {code}
        </Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ 
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      p: 2,
      transform: `scale(${scale}) translate(${position.x}px, ${position.y}px)`,
      transition: 'transform 0.1s ease-out',
      '& svg': {
        maxWidth: '100%',
        maxHeight: '100%',
      }
    }}
      dangerouslySetInnerHTML={{ __html: svgContent }}
    />
  );
};

export default PlantUMLViewer;