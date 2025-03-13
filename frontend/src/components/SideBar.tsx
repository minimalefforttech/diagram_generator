import React, { useState, useEffect, useRef } from 'react';
import { Box, IconButton, Paper, Tooltip } from '@mui/material';
import HistoryIcon from '@mui/icons-material/History';
import ArticleIcon from '@mui/icons-material/Article';
import OutputLog from './OutputLog';
import DiagramHistory, { DiagramHistoryRefHandle } from './DiagramHistory';

interface SideBarProps {
  logs: any[];
  onSelectDiagram: (diagramId: string) => void;
  currentDiagramId?: string;
}

export const SideBar: React.FC<SideBarProps> = ({ 
  logs, 
  onSelectDiagram, 
  currentDiagramId
}) => {
  const [activePanel, setActivePanel] = useState<'logs' | 'history'>('logs');
  const [isExpanded, setIsExpanded] = useState(false);
  const [sidebarWidth, setSidebarWidth] = useState('50%');
  const sidebarRef = useRef<HTMLDivElement>(null);
  const historyRef = useRef<DiagramHistoryRefHandle>(null);
  
  // Update sidebarWidth based on window size
  useEffect(() => {
    const updateWidth = () => {
      const expandWidth = Math.min(window.innerWidth, 600);
      setSidebarWidth(`${expandWidth}px`);
    };

    // Set initial width
    updateWidth();

    // Add resize listener
    window.addEventListener('resize', updateWidth);
    
    // Cleanup
    return () => window.removeEventListener('resize', updateWidth);
  }, []);

  // Method to refresh the history panel - can be called by parent components
  const refreshHistory = () => {
    if (historyRef.current) {
      historyRef.current.refresh();
    }
  };

  return (
    <Paper
      ref={sidebarRef}
      sx={{
        position: 'fixed',
        top: '64px',
        left: 0,
        height: 'calc(100vh - 128px)',
        zIndex: 1000,
        width: isExpanded ? sidebarWidth : '48px',
        transition: 'width 0.3s ease',
        display: 'flex',
        overflow: 'hidden',
        borderRadius: '0 8px 8px 0' // Round the right side
      }}
    >
      <Box
        sx={{
          width: '48px',
          height: '100%',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          pt: 2,
          borderRight: isExpanded ? 1 : 0,
          borderColor: 'divider',
          backgroundColor: 'background.paper',
          zIndex: 1
        }}
      >
        <Tooltip title="History" placement="right">
          <IconButton
            color={activePanel === 'history' ? 'primary' : 'default'}
            onClick={() => {
              setActivePanel('history');
              setIsExpanded(prev => !prev);
              // Refresh history when opening the panel
              if (!isExpanded || activePanel !== 'history') {
                refreshHistory();
              }
            }}
          >
            <HistoryIcon />
          </IconButton>
        </Tooltip>
        <Tooltip title="Logs" placement="right">
          <IconButton
            color={activePanel === 'logs' ? 'primary' : 'default'}
            onClick={() => {
              setActivePanel('logs');
              setIsExpanded(prev => !prev);
            }}
          >
            <ArticleIcon />
          </IconButton>
        </Tooltip>
      </Box>
      <Box 
        sx={{
          flexGrow: 1,
          height: '100%',
          display: isExpanded ? 'flex' : 'none', // Hide only the content panel when collapsed
          flexDirection: 'column',
          overflow: 'hidden',
          backgroundColor: 'background.paper'
        }}
      >
        <Box sx={{
          flexGrow: 1,
          display: 'flex',
          flexDirection: 'column',
          overflow: 'auto',
          scrollbarWidth: 'thin',
          '&::-webkit-scrollbar': {
            width: '8px',
            height: '8px'
          },
          '&::-webkit-scrollbar-thumb': {
            backgroundColor: 'rgba(255, 255, 255, 0.2)',
            borderRadius: '4px',
          },
          '&::-webkit-scrollbar-track': {
            backgroundColor: 'transparent',
          }
        }}>
          {activePanel === 'logs' ? (
            <OutputLog entries={logs} alwaysExpanded={true} />
          ) : (
            <DiagramHistory 
              ref={historyRef}
              onSelectDiagram={(id) => {
                onSelectDiagram(id);
                setIsExpanded(false); // Close sidebar after selecting diagram
              }}
              currentDiagramId={currentDiagramId}
              alwaysExpanded={true}
            />
          )}
        </Box>
      </Box>
    </Paper>
  );
};

// Expose refreshHistory method
export default React.forwardRef<{ refreshHistory: () => void }, SideBarProps>((props, ref) => {
  const historyRef = useRef<DiagramHistoryRefHandle>(null);

  React.useImperativeHandle(ref, () => ({
    refreshHistory: () => {
      if (historyRef.current) {
        historyRef.current.refresh();
      }
    }
  }));

  return <SideBar {...props} />;
});