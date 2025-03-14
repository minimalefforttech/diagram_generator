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
  historyRef?: React.RefObject<DiagramHistoryRefHandle>;
}

// Props for OutputLog component with details dialog state
interface OutputLogWithDetailsState {
  detailsOpen: boolean;
}

export const SideBar: React.FC<SideBarProps> = ({ 
  logs, 
  onSelectDiagram, 
  currentDiagramId,
  historyRef
}) => {
  const [activePanel, setActivePanel] = useState<'logs' | 'history'>('logs');
  const [isExpanded, setIsExpanded] = useState(false);
  const [sidebarWidth, setSidebarWidth] = useState('50%');
  const [outputLogState, setOutputLogState] = useState<OutputLogWithDetailsState>({ detailsOpen: false });
  const sidebarRef = useRef<HTMLDivElement>(null);
  
  // Handle outside click
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (isExpanded && 
          sidebarRef.current && 
          !sidebarRef.current.contains(event.target as Node) && 
          !outputLogState.detailsOpen) {
        setIsExpanded(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isExpanded, outputLogState.detailsOpen]);
  
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
    historyRef?.current?.refresh?.();
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
        transition: 'width 0.3s ease, box-shadow 0.3s ease',
        display: 'flex',
        overflow: 'hidden',
        borderRadius: '0 8px 8px 0', // Round the right side
        boxShadow: isExpanded 
          ? '4px 0px 20px rgba(0, 0, 0, 0.3)' 
          : 'none'
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
            color={(activePanel === 'history' && isExpanded) ? 'primary' : 'default'}
            onClick={() => {
              if (activePanel === 'history') {
                // If already active, toggle expanded state
                setIsExpanded(prev => !prev);
              } else {
                // If not active, set active and expand
                setActivePanel('history');
                setIsExpanded(true);
                refreshHistory();
              }
            }}
          >
            <HistoryIcon />
          </IconButton>
        </Tooltip>
        <Tooltip title="Logs" placement="right">
          <IconButton
            color={(activePanel === 'logs' && isExpanded) ? 'primary' : 'default'}
            onClick={() => {
              if (activePanel === 'logs') {
                // If already active, toggle expanded state
                setIsExpanded(prev => !prev);
              } else {
                // If not active, set active and expand
                setActivePanel('logs');
                setIsExpanded(true);
              }
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
            <OutputLog 
              entries={logs} 
              alwaysExpanded={true}
              onDetailsOpenChange={(open) => setOutputLogState(prev => ({ ...prev, detailsOpen: open }))}
            />
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
  const internalHistoryRef = useRef<DiagramHistoryRefHandle>(null);

  React.useImperativeHandle(ref, () => ({
    refreshHistory: () => {
      if (internalHistoryRef.current) {
        internalHistoryRef.current.refresh();
      }
    }
  }));

  return <SideBar {...props} historyRef={props.historyRef || internalHistoryRef} />;
});
