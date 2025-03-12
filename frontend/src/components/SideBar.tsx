import React, { useState, useEffect, useRef } from 'react';
import { Box, IconButton, Paper, Tooltip } from '@mui/material';
import HistoryIcon from '@mui/icons-material/History';
import ArticleIcon from '@mui/icons-material/Article';
import OutputLog from './OutputLog';
import DiagramHistory from './DiagramHistory';

interface SideBarProps {
  logs: any[];
  onSelectDiagram: (id: string) => void;
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
  
  // Update sidebarWidth based on window size
  useEffect(() => {
    const updateWidth = () => {
      const expandWidth = Math.min(window.innerWidth, 600);
      setSidebarWidth(`${expandWidth}px`);
    };

    // Set initial width
    updateWidth();

    // Add event listener for window resize
    window.addEventListener('resize', updateWidth);

    // Clean up
    return () => window.removeEventListener('resize', updateWidth);
  }, []);

  // Add click outside listener to collapse sidebar when clicking elsewhere
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (isExpanded && 
          sidebarRef.current && 
          !sidebarRef.current.contains(event.target as Node)) {
        setIsExpanded(false);
      }
    };

    // Only add the event listener if sidebar is expanded
    if (isExpanded) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isExpanded]);

  const handleIconClick = (panel: 'logs' | 'history') => {
    if (activePanel === panel && isExpanded) {
      // If clicking on active panel, collapse sidebar
      setIsExpanded(false);
    } else {
      // If clicking on inactive panel or sidebar is collapsed, expand and set active panel
      setActivePanel(panel);
      setIsExpanded(true);
    }
  };

  return (
    <Paper 
      ref={sidebarRef}
      sx={{ 
        position: 'fixed',
        left: 0,
        top: 56 + 8, // Account for header height + margin
        bottom: 56 + 8,
        width: isExpanded ? sidebarWidth : '42px',
        display: 'flex',
        borderRadius: isExpanded ? '0 8px 8px 0' : '0 8px 8px 0',
        overflow: 'hidden',
        transition: 'width 0.3s ease',
        zIndex: 1200,
        flexDirection: 'row-reverse', // Icons on the right side
        boxShadow: 3
      }}
    >
      {/* Icons Panel - on the right side */}
      <Box sx={{ 
        width: 48, 
        borderLeft: 1,
        borderColor: 'divider',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        pt: 2,
        gap: 1,
        bgcolor: 'background.paper',
        zIndex: 2 // Make sure icons stay on top
      }}>
        <Tooltip title="Logs" placement="left">
          <IconButton 
            onClick={() => handleIconClick('logs')}
            color={activePanel === 'logs' && isExpanded ? 'primary' : 'default'}
          >
            <ArticleIcon />
          </IconButton>
        </Tooltip>
        <Tooltip title="History" placement="left">
          <IconButton 
            onClick={() => handleIconClick('history')}
            color={activePanel === 'history' && isExpanded ? 'primary' : 'default'}
          >
            <HistoryIcon />
          </IconButton>
        </Tooltip>
      </Box>

      {/* Content Panel */}
      <Box sx={{ 
        flexGrow: 1,
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
        height: '100%'
      }}>
        <Box sx={{
          flexGrow: 1,
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

export default SideBar;