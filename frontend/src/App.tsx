import { useEffect, useState, useRef } from 'react';
import { Box, CssBaseline } from '@mui/material';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Layout } from './components';
import { diagramService } from './services/api';
import { DiagramState, LogEntry } from './types';
import { ToastContainer, toast } from 'react-toastify';
import { ErrorToast } from './components/ErrorToast';
import 'react-toastify/dist/ReactToastify.css';
import ConfigurationScreen from './components/ConfigurationScreen';
import { ThemeProvider } from './contexts/ThemeContext';
import { UIPreferencesProvider } from './contexts/UIPreferencesContext';
import SideBar from './components/SideBar';

const App: React.FC = () => {
  const [diagram, setDiagram] = useState<DiagramState>({
    loading: false
  });
  const [currentScreen, setCurrentScreen] = useState<'configuration' | 'workspace'>('configuration');
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [agentIterations, setAgentIterations] = useState(0);
  const [currentType, setCurrentType] = useState<string>('auto');
  const queryClient = new QueryClient();
  
  // Reference to the SideBar component to access its methods
  const sidebarRef = useRef<{ refreshHistory: () => void }>(null);

  const loadInitialContext = async () => {
    // Load initial logs
    const initialLogs = await diagramService.getLogs();
    setLogs(initialLogs);
    // Set up log polling
    setInterval(async () => {
      const subsequentLogs = await diagramService.getLogs();
      setLogs(subsequentLogs);
    }, 5000);
  };

  useEffect(() => {
    loadInitialContext();
  }, []);

  const handleCreateDiagram = async (description: string, model: string, syntax: string = 'mermaid', diagramType?: string) => {
    setDiagram({
      loading: true,
      error: undefined,
      code: undefined
    });
    
    setCurrentType(diagramType || 'auto');

    try {
      // First switch to workspace screen - this allows the diagram component to be mounted
      // before we try to render the diagram
      setCurrentScreen('workspace');
      
      const response = await diagramService.generateDiagram({
        description,
        model,
        syntax,
        diagramType,
        options: {
          agent: { enabled: true }
        }
      });

      // Now update the diagram data after the component is mounted
      setDiagram({
        loading: false,
        code: response.code,
        error: undefined,
        id: response.id
      });
      
      if (response.id) {
        const iterations = await diagramService.getAgentIterations(response.id);
        setAgentIterations(iterations);
        
        // Refresh the history list after successful diagram creation
        if (sidebarRef.current) {
          sidebarRef.current.refreshHistory();
        }
      }
    } catch (err: any) {
      // Extract HTTP status code for Axios errors
      const statusCode = err.response?.status;
      const statusText = err.response?.statusText;
      const statusDisplay = statusCode ? ` (${statusCode}${statusText ? ` ${statusText}` : ''})` : '';
      
      const errorMessage = (err.error || (err.response?.data?.error) || 'Failed to generate diagram') + statusDisplay;
      const errorDetails = err.details || err.response?.data || (err.message && { message: err.message });
      
      setDiagram({
        loading: false,
        error: errorMessage
      });
      toast.error(<ErrorToast message={errorMessage} details={errorDetails} />);
    }
  };

  const handleRequestChanges = async (message: string, model: string) => {
    if (!diagram.code) {
      toast.error(<ErrorToast message="No diagram to update" />);
      return;
    }
    
    setDiagram(prev => ({
      ...prev,
      loading: true,
      error: undefined
    }));

    try {
      const response = await diagramService.requestChanges(diagram.id || 'current', {
        description: message,
        model,
        diagramType: currentType.toLowerCase(),
        options: {
          agent: { enabled: true },
        },
      });

      setDiagram(prev => ({
        ...prev,
        loading: false,
        code: response.code,
        error: undefined,
        id: response.id || prev.id
      }));
      
      if (response.id || diagram.id) {
        const iterations = await diagramService.getAgentIterations(response.id || diagram.id || 'current');
        setAgentIterations(iterations);
        
        // Refresh the history list after successful diagram update
        if (sidebarRef.current) {
          sidebarRef.current.refreshHistory();
        }
      }
    } catch (err: any) {
      // Extract HTTP status code for Axios errors
      const statusCode = err.response?.status;
      const statusText = err.response?.statusText;
      const statusDisplay = statusCode ? ` (${statusCode}${statusText ? ` ${statusText}` : ''})` : '';
      
      const errorMessage = (err.error || (err.response?.data?.error) || 'Failed to update diagram') + statusDisplay;
      const errorDetails = err.details || err.response?.data || (err.message && { message: err.message });
      
      setDiagram(prev => ({
        ...prev,
        loading: false,
        error: errorMessage
      }));
      toast.error(<ErrorToast message={errorMessage} details={errorDetails} />);
    }
  };

  const handleLoadDiagram = async (diagramId: string) => {
    setDiagram(prev => ({
      ...prev,
      loading: true,
      error: undefined
    }));
    
    // First make sure we're in workspace screen
    setCurrentScreen('workspace');
    
    try {
      const loadedDiagram = await diagramService.getDiagramById(diagramId);
      
      // Now update the diagram data
      setDiagram({
        loading: false,
        code: loadedDiagram.code,
        error: undefined,
        id: diagramId
      });
      
      // Fetch agent iterations
      const iterations = await diagramService.getAgentIterations(diagramId);
      setAgentIterations(iterations);
      
      toast.success('Diagram loaded from history');
    } catch (err: any) {
      console.error('Failed to load diagram:', err);
      
      // Extract HTTP status code for Axios errors
      const statusCode = err.response?.status;
      const statusText = err.response?.statusText;
      const statusDisplay = statusCode ? ` (${statusCode}${statusText ? ` ${statusText}` : ''})` : '';
      
      const errorMessage = (err.error || (err.response?.data?.error) || 'Failed to load diagram from history') + statusDisplay;
      const errorDetails = err.details || err.response?.data || (err.message && { message: err.message });
      
      setDiagram(prev => ({
        ...prev,
        loading: false,
        error: errorMessage
      }));
      toast.error(<ErrorToast message={errorMessage} details={errorDetails} />);
    }
  };

  const handleClearLogs = async () => {
    try {
      await diagramService.clearLogs();
      setLogs([]);
      toast.success('Logs cleared');
    } catch (error) {
      toast.error('Failed to clear logs');
    }
  };

  const handleNewDiagram = () => {
    setDiagram({
      loading: false,
      code: undefined,
      error: undefined,
      id: undefined
    });
    setAgentIterations(0);
    setCurrentScreen('configuration');
  };
  
  const handleStartDiagramGeneration = (config: any) => {
    handleCreateDiagram(
      config.description,
      config.model,
      config.syntax,
      config.diagramType
    );
  };

  return (
    <ThemeProvider>
      <UIPreferencesProvider>
        <QueryClientProvider client={queryClient}>
          <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
            <CssBaseline />
            
            {currentScreen === 'configuration' && (
              <ConfigurationScreen onStartDiagramGeneration={handleStartDiagramGeneration} />
            )}
            
            {currentScreen === 'workspace' && (
              <Layout
                diagram={diagram}
                logs={logs}
                agentIterations={agentIterations}
                onRequestChanges={handleRequestChanges}
                onNewDiagram={handleNewDiagram}
                onClearLogs={handleClearLogs}
                onLoadDiagram={handleLoadDiagram}
                onSyntaxChange={() => {}} // Remove unused parameter
                onTypeChange={setCurrentType}
                onCodeChange={(code) => setDiagram(prev => ({ ...prev, code }))}
              />
            )}
            
            {/* SideBar visible across all screens */}
            <SideBar
              ref={sidebarRef}
              logs={logs}
              onSelectDiagram={handleLoadDiagram}
              currentDiagramId={diagram.id}
            />
            
            <ToastContainer position="bottom-right" />
          </Box>
        </QueryClientProvider>
      </UIPreferencesProvider>
    </ThemeProvider>
  );
};

export default App;
