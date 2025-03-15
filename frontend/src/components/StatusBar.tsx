import React from 'react';
import { Box, Typography, Tooltip, IconButton } from '@mui/material';
import RestartAltIcon from '@mui/icons-material/RestartAlt';
import type { ZoomPanHook } from '../hooks/useZoomPan';

interface StatusBarProps {
  zoomPan: ZoomPanHook;
}

const StatusBar: React.FC<StatusBarProps> = ({ zoomPan }) => {
  const zoomPercent = Math.round(zoomPan.scale * 100);
  const { x, y } = zoomPan.position;

  return (
    <Box sx={{
      position: 'absolute',
      bottom: 8,
      left: 8,
      zIndex: 1,
      backgroundColor: 'rgba(255, 255, 255, 0.8)',
      borderRadius: 1,
      px: 1,
      py: 0.5,
      display: 'flex',
      alignItems: 'center',
      gap: 2,
      boxShadow: 1
    }}>
      <Tooltip title="Reset view (R)">
        <IconButton
          onClick={zoomPan.reset}
          size="small"
          sx={{ p: 0.5 }}
        >
          <RestartAltIcon fontSize="small" />
        </IconButton>
      </Tooltip>

      <Typography variant="body2" color="text.secondary" sx={{ 
        fontFamily: 'monospace',
        fontSize: '0.8rem',
        whiteSpace: 'nowrap'
      }}>
        {zoomPercent}% • X:{Math.round(x)} Y:{Math.round(y)}
      </Typography>
    </Box>
  );
};

export default StatusBar;
