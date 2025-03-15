import React, { useState } from 'react';
import { Box, Typography, IconButton, Tooltip, useTheme } from '@mui/material';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import CheckIcon from '@mui/icons-material/Check';

interface ErrorToastProps {
  message: string;
  details?: any;
}

export const ErrorToast: React.FC<ErrorToastProps> = ({ message, details }) => {
  const [copied, setCopied] = useState(false);
  const theme = useTheme();
  
  const handleCopyError = () => {
    const errorText = JSON.stringify({ message, details }, null, 2);
    navigator.clipboard.writeText(errorText)
      .then(() => {
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
      })
      .catch(err => console.error('Failed to copy error details:', err));
  };

  return (
    <Box 
      sx={{ 
        display: 'flex', 
        alignItems: 'flex-start',
        gap: 1,
      }}
    >
      <Typography sx={{ flex: 1 }}>{message}</Typography>
      <Tooltip title={copied ? "Copied!" : "Copy error details"}>
        <IconButton 
          size="small" 
          onClick={handleCopyError}
          sx={{ 
            color: copied 
              ? 'success.main' 
              : theme.palette.mode === 'dark' 
                ? 'primary.light' 
                : 'primary.main',
            transition: 'all 0.2s',
            mt: -0.5,
            mr: -0.5
          }}
        >
          {copied ? <CheckIcon fontSize="small" /> : <ContentCopyIcon fontSize="small" />}
        </IconButton>
      </Tooltip>
    </Box>
  );
};