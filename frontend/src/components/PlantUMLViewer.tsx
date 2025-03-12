import React from 'react';
import { Box, Typography } from '@mui/material';

interface PlantUMLViewerProps {
  code: string;
  onError?: (error: string) => void;
}

// Placeholder component for PlantUML rendering
// TODO: Implement actual PlantUML rendering when backend support is added
const PlantUMLViewer: React.FC<PlantUMLViewerProps> = ({ code, onError }) => {
  React.useEffect(() => {
    if (onError) {
      onError('PlantUML rendering not yet implemented');
    }
  }, [code, onError]);

  return (
    <Box sx={{ p: 2 }}>
      <Typography variant="body2" component="pre" sx={{ 
        whiteSpace: 'pre-wrap',
        fontFamily: 'monospace',
        fontSize: '0.9rem'
      }}>
        {code}
      </Typography>
    </Box>
  );
};

export default PlantUMLViewer;