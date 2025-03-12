import { useEffect, useState } from 'react';
import { Box, CssBaseline } from '@mui/material';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Layout } from './components';
import { diagramService } from './services/api';
import { DiagramState, LogEntry } from './types';
import { ToastContainer, toast } from 'react-toastify';
import { ErrorToast } from './components/ErrorToast';
import 'react-toastify/dist/ReactToastify.css';
import ConfigurationScreen from './components/ConfigurationScreen';

const App: React.FC = () => {
  const [diagram, setDiagram] = useState<DiagramState>({
    loading: false
  });
  const [currentScreen, setCurrentScreen] = useState<'configuration' | 'workspace'>('configuration');
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [agentIterations, setAgentIterations] = useState(0);
  const [currentSyntax, setCurrentSyntax] = useState<string>('mermaid');
  const [currentType, setCurrentType] = useState<string>('auto');
  const queryClient = new QueryClient();

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
    
    setCurrentSyntax(syntax);
    setCurrentType(diagramType || 'auto');

    try {
      const response = await diagramService.generateDiagram({
        description,
        type: syntax.toLowerCase(),
        diagram_subtype: diagramType?.toLowerCase() || 'auto',
        model,
        options: {
          agent: { enabled: true },
        },
      });
      
      setDiagram({
        loading: false,
        code: response.code,
        error: undefined,
        id: response.id
      });
      
      setCurrentScreen('workspace');
      
      if (response.id) {
        const iterations = await diagramService.getAgentIterations(response.id);
        setAgentIterations(iterations);
      }
    } catch (err: any) {
      const errorMessage = err.error || 'Failed to generate diagram';
      setDiagram({
        loading: false,
        error: errorMessage,
        code: undefined
      });
      toast.error(<ErrorToast message={errorMessage} details={err.details} />);
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
        type: currentSyntax.toLowerCase() ,
        diagram_subtype: currentType.toLowerCase(),
        model,
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
      }
    } catch (err: any) {
      const errorMessage = err.error || 'Failed to update diagram';
      setDiagram(prev => ({
        ...prev,
        loading: false,
        error: errorMessage
      }));
      toast.error(<ErrorToast message={errorMessage} details={err.details} />);
    }
  };

  const handleLoadDiagram = async (diagramId: string) => {
    setDiagram(prev => ({
      ...prev,
      loading: true,
      error: undefined
    }));
    
    try {
      const loadedDiagram = await diagramService.getDiagramById(diagramId);
      
      setDiagram({
        loading: false,
        code: loadedDiagram.code,
        error: undefined,
        id: diagramId
      });
      
      // Fetch agent iterations
      const iterations = await diagramService.getAgentIterations(diagramId);
      setAgentIterations(iterations);
      
      // Make sure we're in workspace screen
      setCurrentScreen('workspace');
      
      toast.success('Diagram loaded from history');
    } catch (error) {
      console.error('Failed to load diagram:', error);
      toast.error('Failed to load diagram from history');
      
      setDiagram(prev => ({
        ...prev,
        loading: false,
        error: 'Failed to load diagram'
      }));
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
            onSyntaxChange={setCurrentSyntax}
            onTypeChange={setCurrentType}
            onCodeChange={(code) => setDiagram(prev => ({ ...prev, code }))}
          />
        )}
        
        <ToastContainer position="bottom-right" />
      </Box>
    </QueryClientProvider>
  );
};

export default App;
