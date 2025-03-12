import React, { useState, useEffect } from 'react';
import { Box, CssBaseline } from '@mui/material';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Layout } from './components';
import { diagramService } from './services/api';
import { DiagramState, LogEntry } from './types';
import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

const queryClient = new QueryClient();

function App() {
  const [diagram, setDiagram] = useState<DiagramState>({
    loading: false
  });
  const [logs, setLogs] = useState<LogEntry[]>([]);

  // Poll for new logs
  useEffect(() => {
    const fetchLogs = async () => {
      const newLogs = await diagramService.getLogs();
      setLogs(newLogs);
    };

    const interval = setInterval(fetchLogs, 2000);
    return () => clearInterval(interval);
  }, []);

  const handleCreateDiagram = async (description: string, model: string) => {
    setDiagram({
      loading: true,
      error: undefined,
      code: undefined
    });

    try {
      const response = await diagramService.generateDiagram({
        description,
        type: 'mermaid',
        model,
        options: {
          agent: { enabled: true },
        },
      });
      
      setDiagram({
        loading: false,
        code: response.code,
        error: undefined
      });
    } catch (err: any) {
      const errorMessage = err.error || 'Failed to generate diagram';
      setDiagram({
        loading: false,
        error: errorMessage,
        code: undefined
      });
      toast.error(errorMessage);
    }
  };

  const handleRequestChanges = async (message: string, model: string) => {
    if (!diagram.code) {
      toast.error('No diagram to update');
      return;
    }

    setDiagram(prev => ({
      ...prev,
      loading: true,
      error: undefined
    }));

    try {
      const response = await diagramService.requestChanges('current', {
        description: message,
        type: 'mermaid',
        model,
        options: {
          agent: { enabled: true },
        },
      });

      setDiagram(prev => ({
        ...prev,
        loading: false,
        code: response.code,
        error: undefined
      }));
    } catch (err: any) {
      const errorMessage = err.error || 'Failed to update diagram';
      setDiagram(prev => ({
        ...prev,
        loading: false,
        error: errorMessage
      }));
      toast.error(errorMessage);
    }
  };

  const handleNewDiagram = () => {
    setDiagram({
      loading: false,
      code: undefined,
      error: undefined
    });
  };

  return (
    <QueryClientProvider client={queryClient}>
      <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
        <CssBaseline />
        <Layout
          diagram={diagram}
          logs={logs}
          onCreateDiagram={handleCreateDiagram}
          onRequestChanges={handleRequestChanges}
          onNewDiagram={handleNewDiagram}
        />
        <ToastContainer
          position="bottom-right"
          theme="dark"
          autoClose={5000}
        />
      </Box>
    </QueryClientProvider>
  );
}

export default App;
