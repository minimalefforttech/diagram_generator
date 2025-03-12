import React, { useState } from 'react';
import { Box, Typography, IconButton, Tooltip } from '@mui/material';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import { green, red } from '@mui/material/colors';

interface ErrorToastProps {
  message: string;
  details?: any;
}

export const ErrorToast: React.FC<ErrorToastProps> = ({ message, details }) => {
  const [copied, setCopied] = useState(false);
  const hasDetails = details && Object.keys(details).length > 0;

  const handleCopyError = () => {
    if (!hasDetails) return;
    
    const errorText = JSON.stringify({ message, details }, null, 2);
    navigator.clipboard.writeText(errorText).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  return (
    <Box 
      sx={{ 
        display: 'flex', 
        alignItems: 'flex-start',
        gap: 1,
        cursor: hasDetails ? 'pointer' : 'default',
        '&:hover': hasDetails ? {
          '& .copy-button': {
            opacity: 1
          }
        } : {}
      }}
      onClick={handleCopyError}
    >
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flex: 1 }}>
        <ErrorIcon sx={{ color: red[500], fontSize: 20 }} />
        <Typography>{message}</Typography>
      </Box>
      {hasDetails && (
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, ml: 'auto' }}>
          {copied ? (
            <Typography 
              variant="caption" 
              sx={{ 
                color: green[500],
                display: 'flex',
                alignItems: 'center',
                gap: 0.5
              }}
            >
              <CheckCircleIcon fontSize="small" />
              Copied
            </Typography>
          ) : (
            <Tooltip title="Copy error details">
              <IconButton 
                size="small" 
                className="copy-button"
                sx={{ 
                  opacity: 0,
                  transition: 'opacity 0.2s'
                }}
              >
                <ContentCopyIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          )}
        </Box>
      )}
    </Box>
  );
};