import React, { useState } from 'react';
import { 
  Box, 
  Container, 
  Typography,
  Button,
  Chip,
  Tooltip
} from '@mui/material';
import { DiagramState } from '../types';
import DiagramPanel from './DiagramPanel';
import ChatPanel from './ChatPanel';
import { useUIPreferences } from '../contexts/UIPreferencesContext';
import ThemeToggle from './ThemeToggle';
import BarChartIcon from '@mui/icons-material/BarChart';
import DeleteIcon from '@mui/icons-material/Delete';
import AddIcon from '@mui/icons-material/Add';

export interface LayoutProps {
  diagram: DiagramState;
  logs: any[];
  agentIterations: number;
  onRequestChanges: (message: string, model: string, updateCurrent?: boolean) => void;
  onNewDiagram: () => void;
  onClearLogs: () => void;
  onLoadDiagram: (id: string) => void;
  onSyntaxChange: (syntax: string) => void;
  onTypeChange: (type: string) => void;
  onCodeChange: (code: string) => void;
  syntax: string; // Added prop
  diagramType: string; // Added prop
  ragEnabled?: boolean;
  ragDirectory?: string;
  onRagDirectoryChange?: (directory: string) => void;
}

const Layout: React.FC<LayoutProps> = ({
  diagram,
  logs,
  agentIterations,
  onRequestChanges,
  onNewDiagram,
  onClearLogs,
  onLoadDiagram,
  onSyntaxChange,
  onTypeChange,
  onCodeChange,
  syntax,
  diagramType,
  ragEnabled = false,
  ragDirectory = '',
  onRagDirectoryChange
}) => {
  const { preferences } = useUIPreferences();
  const [showCodeEditor, setShowCodeEditor] = useState<boolean>(false);

  const toggleCodeEditor = () => {
    setShowCodeEditor(prev => !prev);
  };

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        height: '100vh',
        width: '100vw',
        overflow: 'hidden'
      }}
    >
      {/* Header */}
      <Box sx={{ 
        py: 1, 
        px: 2, 
        display: 'flex', 
        justifyContent: 'space-between',
        alignItems: 'center',
        borderBottom: '1px solid rgba(255, 255, 255, 0.12)',
        flexShrink: 0,
        zIndex: 1100
      }}>
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <Typography variant="h6" component="div">
            Diagram Generator
          </Typography>
          {diagram.id && (
            <Tooltip title="Agent iterations">
              <Chip 
                size="small" 
                icon={<BarChartIcon fontSize="small" />} 
                label={`Iterations: ${agentIterations}`} 
                sx={{ ml: 2 }}
              />
            </Tooltip>
          )}
        </Box>
        
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <ThemeToggle />
          
          <Button 
            variant="contained" 
            color="primary" 
            startIcon={<AddIcon />}
            onClick={onNewDiagram}
          >
            New Diagram
          </Button>
        </Box>
      </Box>
      
      {/* Main Content */}
      <Container 
        maxWidth={false}
        className="main-container"
        sx={{ 
          flexGrow: 1,
          height: 'calc(100vh - 56px)', // Account for header height
          py: 2,
          overflow: 'hidden',
          position: 'relative',
          pl: '56px', // Add left padding to account for sidebar icons
        }}
      >
        {/* Main Content Area */}
        <Box 
          sx={{ 
            height: '100%',
            display: 'flex',
            gap: 2
          }}
        >
          {/* Diagram Panel */}
          <Box 
            sx={{ 
              flexGrow: 1,
              height: '100%',
              display: 'flex',
              flexDirection: 'column',
              minWidth: 0
            }}
          >
            <DiagramPanel
              code={diagram.code}
              loading={diagram.loading}
              error={diagram.error}
              showCodeEditor={showCodeEditor}
              onCodeChange={onCodeChange}
              onSyntaxChange={onSyntaxChange}
              onTypeChange={onTypeChange}
              onToggleCodeEditor={toggleCodeEditor}
              syntax={syntax}
              diagramType={diagramType}
            />
          </Box>

          {/* Chat Panel */}
          <Box sx={{ 
            width: '400px',
            flexShrink: 0
          }}>
            <ChatPanel
              currentDiagram={diagram.code}
              onRequestChanges={onRequestChanges}
              onSyntaxChange={onSyntaxChange}
              onTypeChange={onTypeChange}
              onRagDirectoryChange={onRagDirectoryChange}
              ragEnabled={ragEnabled}
            />
          </Box>
        </Box>
      </Container>
    </Box>
  );
};

export default Layout;
