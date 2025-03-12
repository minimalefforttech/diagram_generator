import React from 'react';
import { Box, Container, CssBaseline, Grid, ThemeProvider, createTheme } from '@mui/material';
import { DiagramState, LogEntry } from '../types';
import DiagramPanel from './DiagramPanel';
import ChatPanel from './ChatPanel';
import OutputLog from './OutputLog';

const darkTheme = createTheme({
  palette: {
    mode: 'dark',
  },
});

export interface LayoutProps {
  diagram: DiagramState;
  logs: LogEntry[];
  onCreateDiagram: (description: string, model: string) => void;
  onRequestChanges: (message: string, model: string) => void;
  onNewDiagram: () => void;
}

const Layout: React.FC<LayoutProps> = ({
  diagram,
  logs,
  onCreateDiagram,
  onRequestChanges,
  onNewDiagram,
}) => {
  return (
    <ThemeProvider theme={darkTheme}>
      <CssBaseline />
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          height: '100vh',
          overflow: 'hidden'
        }}
      >
        <Container maxWidth={false} sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column', py: 2 }}>
          <Grid container spacing={2} sx={{ flexGrow: 1, height: '100%' }}>
            {/* Left side: Diagram */}
            <Grid item xs={12} md={8} sx={{ height: '100%' }}>
              <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column', gap: 2 }}>
                <DiagramPanel
                  code={diagram.code}
                  loading={diagram.loading}
                  error={diagram.error}
                />
                <OutputLog entries={logs} />
              </Box>
            </Grid>

            {/* Right side: Interaction Panel */}
            <Grid item xs={12} md={4} sx={{ height: '100%' }}>
              <ChatPanel
                currentDiagram={diagram.code}
                onRequestChanges={onRequestChanges}
                onNewDiagram={onNewDiagram}
                onCreateDiagram={onCreateDiagram}
              />
            </Grid>
          </Grid>
        </Container>
      </Box>
    </ThemeProvider>
  );
};

export default Layout;
