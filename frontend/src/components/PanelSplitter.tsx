import React from 'react';
import { Box } from '@mui/material';
import DragHandleIcon from '@mui/icons-material/DragHandle';

interface PanelSplitterProps {
  onMouseDown: (e: React.MouseEvent) => void;
  orientation?: 'vertical' | 'horizontal';
}

const PanelSplitter: React.FC<PanelSplitterProps> = ({ 
  onMouseDown,
  orientation = 'vertical'
}) => {
  const isVertical = orientation === 'vertical';
  
  return (
    <Box
      sx={{
        position: 'absolute',
        ...(isVertical ? {
          left: -2,
          top: 0,
          bottom: 0,
          width: 4,
          cursor: 'col-resize',
        } : {
          bottom: -2,
          left: 0,
          right: 0,
          height: 4,
          cursor: 'row-resize',
        }),
        bgcolor: 'divider',
        '&:hover': {
          bgcolor: 'primary.main',
        },
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 10
      }}
      onMouseDown={onMouseDown}
    >
      <DragHandleIcon 
        sx={{ 
          transform: isVertical ? 'rotate(90deg)' : 'none',
          opacity: 0.5,
          '&:hover': { opacity: 1 }
        }} 
      />
    </Box>
  );
};

export default PanelSplitter;