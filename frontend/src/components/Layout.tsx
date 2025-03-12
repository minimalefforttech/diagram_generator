import React, { useState } from 'react';
import { 
  Box, 
  Container, 
  Grid, 
  Typography,
  Button,
  Chip,
  IconButton,
  Tooltip
} from '@mui/material';
import { DiagramState } from '../types';
import DiagramPanel from './DiagramPanel';
import ChatPanel from './ChatPanel';
import OutputLog from './OutputLog';
import DiagramHistory from './DiagramHistory';
import CodeIcon from '@mui/icons-material/Code';
import BarChartIcon from '@mui/icons-material/BarChart';
import DeleteIcon from '@mui/icons-material/Delete';
import AddIcon from '@mui/icons-material/Add';

export interface LayoutProps {
  diagram: DiagramState;
  logs: any[];
  agentIterations: number;
  onRequestChanges: (message: string, model: string) => void;
  onNewDiagram: () => void;
  onClearLogs: () => void;
  onLoadDiagram: (id: string) => void;
  onSyntaxChange: (syntax: string) => void;
  onTypeChange: (type: string) => void;
  onCodeChange: (code: string) => void;
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
  onCodeChange
}) => {
  const [showCodeEditor, setShowCodeEditor] = useState<boolean>(false);

  const toggleCodeEditor = () => {
    setShowCodeEditor(prev => !prev);
  };

  const handleSelectDiagram = (diagramId: string) => {
    if (onLoadDiagram) {
      onLoadDiagram(diagramId);
    }
  };

  const handleSyntaxChange = (syntax: string) => {
    if (onSyntaxChange) {
      onSyntaxChange(syntax);
    }
  };

  const handleTypeChange = (type: string) => {
    if (onTypeChange) {
      onTypeChange(type);
    }
  };

  const handleCodeChange = (code: string) => {
    if (onCodeChange) {
      onCodeChange(code);
    }
  };

  return (
    <>
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          height: '100vh',
          overflow: 'hidden'
        }}
      >
        <Box sx={{ 
          py: 1, 
          px: 2, 
          display: 'flex', 
          justifyContent: 'space-between',
          alignItems: 'center',
          borderBottom: '1px solid rgba(255, 255, 255, 0.12)',
          flexShrink: 0
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
            <Tooltip title={showCodeEditor ? "Show Diagram View" : "Show Code Editor"}>
              <IconButton onClick={toggleCodeEditor} color="primary">
                <CodeIcon />
              </IconButton>
            </Tooltip>
            
            <Button 
              variant="outlined" 
              color="error" 
              startIcon={<DeleteIcon />}
              onClick={onClearLogs}
            >
              Clear Logs
            </Button>
            
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
        
        <Container maxWidth={false} sx={{ flexGrow: 1, minHeight: 0, py: 2 }}>
          <Grid container spacing={2} sx={{ height: '100%' }}>
            {/* Left side: Diagram */}
            <Grid item xs={12} md={8} sx={{ height: '100%', minHeight: 0 }}>
              <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column', gap: 2, minHeight: 0 }}>
                <DiagramPanel
                  code={diagram.code}
                  loading={diagram.loading}
                  error={diagram.error}
                  showCodeEditor={showCodeEditor}
                  onCodeChange={handleCodeChange}
                  onSyntaxChange={handleSyntaxChange}
                  onTypeChange={handleTypeChange}
                />
                <OutputLog entries={logs} />
              </Box>
            </Grid>

            {/* Right side: Interaction Panel */}
            <Grid item xs={12} md={4} sx={{ height: '100%', minHeight: 0, display: 'flex', flexDirection: 'column', gap: 2 }}>
              <ChatPanel
                currentDiagram={diagram.code}
                onRequestChanges={onRequestChanges}
                onNewDiagram={onNewDiagram}
              />
              <DiagramHistory 
                onSelectDiagram={handleSelectDiagram}
                currentDiagramId={diagram.id}
              />
            </Grid>
          </Grid>
        </Container>
      </Box>
    </>
  );
};

export default Layout;
