import React, { useState, useEffect } from 'react';
import { Box, CircularProgress, Typography, Alert, Link, AlertTitle } from '@mui/material';
import { generatePlantUMLPngUrlAsync } from '../lib/plantuml-encoder';

interface PlantUMLViewerProps {
  code?: string;
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
  const [error, setError] = useState<string | null>(null);
  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const [retryCount, setRetryCount] = useState(0);
  const [imageLoaded, setImageLoaded] = useState(false);

  // Helper to check if error is a Java dependency error
  const isJavaDependencyError = (error: string): boolean => {
    const lowerError = error.toLowerCase();
    return lowerError.includes('java is not') || 
           lowerError.includes('java not found') ||
           lowerError.includes("'java' is not recognized");
  };

  // Helper to check if error is a syntax error
  const isSyntaxError = (error: string): boolean => {
    const lowerError = error.toLowerCase();
    return lowerError.includes('syntax error') ||
           lowerError.includes('@startuml') ||
           lowerError.includes('@enduml') ||
           lowerError.includes('unexpected line') ||
           lowerError.includes('bad tree definition') ||
           lowerError.includes('failed to generate valid diagram');
  };

  // Generate diagram URL when code changes
  useEffect(() => {
    const generateDiagram = async () => {
      if (!code) {
        setImageUrl(null);
        setLoading(false);
        setError(null);
        setImageLoaded(false);
        return;
      }

      try {
        setLoading(true);
        setError(null);
        setImageLoaded(false);
        
        const url = await generatePlantUMLPngUrlAsync(code);
        
        setImageUrl(url);
        setImageLoaded(true);
        setError(null);
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to generate diagram';
        console.error('PlantUML rendering error:', errorMessage);
        
        // Only retry on network/server errors, not on validation failures
        if ((errorMessage.includes('500') || errorMessage.includes('Failed to load')) && retryCount < 3) {
          console.log(`Retrying PlantUML render (attempt ${retryCount + 1})`);
          setTimeout(() => {
            setRetryCount(prev => prev + 1);
          }, 1000);
          return;
        }
        
        setError(errorMessage);
        setImageUrl(null);
        setImageLoaded(false);
        if (onError) {
          onError(errorMessage);
        }
      } finally {
        setLoading(false);
      }
    };

    generateDiagram();
  }, [code, onError, retryCount]);

  if (loading) {
    return (
      <Box sx={{ display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', p: 4, gap: 2 }}>
        <CircularProgress />
        <Typography variant="body2" color="textSecondary">
          Generating diagram...
        </Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ p: 2 }}>
        {isJavaDependencyError(error) ? (
          <Alert 
            severity="warning" 
            sx={{ mb: 2 }}
          >
            <AlertTitle>Java Required</AlertTitle>
            <Typography variant="body1" gutterBottom>
              Java is required to render PlantUML diagrams but was not found on your system.
            </Typography>
            <Typography variant="body2">
              Please install Java and make sure it's available in your system PATH.&nbsp;
              <Link 
                href="https://adoptium.net" 
                target="_blank" 
                rel="noopener noreferrer"
              >
                Download Java here
              </Link>
            </Typography>
          </Alert>
        ) : isSyntaxError(error) ? (
          <Alert 
            severity="error" 
            sx={{ mb: 2 }}
          >
            <AlertTitle>Syntax Error</AlertTitle>
            <Typography variant="body1" gutterBottom>
              {error}
            </Typography>
            <Typography variant="body2">
              Common issues:
              <ul>
                <li>Missing @startuml/@enduml tags</li>
                <li>Invalid diagram type or syntax</li>
                <li>Malformed relationships or connections</li>
              </ul>
              <Link 
                href="https://plantuml.com/guide" 
                target="_blank" 
                rel="noopener noreferrer"
              >
                View PlantUML guide
              </Link>
            </Typography>
          </Alert>
        ) : (
          <Alert 
            severity="error" 
            sx={{ mb: 2 }}
          >
            <AlertTitle>Error</AlertTitle>
            <Typography variant="body1">
              {error}
            </Typography>
          </Alert>
        )}
        
        <Typography variant="subtitle2" sx={{ mt: 2, mb: 1 }}>
          Diagram Code:
        </Typography>
        <Typography variant="body2" component="pre" sx={{ 
          whiteSpace: 'pre-wrap',
          fontFamily: 'monospace',
          fontSize: '0.9rem',
          p: 2,
          bgcolor: 'background.paper',
          borderRadius: 1,
          border: '1px solid',
          borderColor: 'divider'
        }}>
          {code}
        </Typography>
      </Box>
    );
  }

  return (
    <Box 
      sx={{ 
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        width: '100%',
        height: '100%',
        overflow: 'hidden'
      }}
    >
      {imageUrl && (
        <img
          src={imageUrl}
          alt="PlantUML Diagram"
          style={{
            maxWidth: '100%',
            maxHeight: '100%',
            transform: `scale(${scale}) translate(${position.x}px, ${position.y}px)`,
            transition: 'transform 0.1s ease-out',
            opacity: imageLoaded ? 1 : 0,
          }}
          draggable={false}
          onLoad={() => setImageLoaded(true)}
          onError={(e) => {
            console.error('Image loading error:', e);
            setError('Failed to load diagram image. The diagram syntax may be incorrect.');
            if (onError) {
              onError('Failed to load diagram image. The diagram syntax may be incorrect.');
            }
          }}
        />
      )}
    </Box>
  );
};

export default PlantUMLViewer;
