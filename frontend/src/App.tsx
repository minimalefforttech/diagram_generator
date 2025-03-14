import { useEffect, useState, useRef } from 'react';
import { Box, CssBaseline } from '@mui/material';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Layout } from './components';
import { diagramService, logError } from './services/api';
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
  const [agentIterations, setAgentIterations] = useState<number>(0);
  const [currentSyntax, setCurrentSyntax] = useState<string>('mermaid');
  const [currentType, setCurrentType] = useState<string>('auto');
  const [ragEnabled, setRagEnabled] = useState<boolean>(false);
  const [ragDirectory, setRagDirectory] = useState<string>('');
  const queryClient = new QueryClient();
  
  // Reference to the SideBar component to access its methods
  const sidebarRef = useRef<{ refreshHistory: () => void }>(null);

  const loadInitialContext = async () => {
    try {
      // Load initial logs
      const initialLogs = await diagramService.getLogs();
      setLogs(initialLogs);
      // Set up log polling
      setInterval(async () => {
        const subsequentLogs = await diagramService.getLogs();
        setLogs(subsequentLogs);
      }, 5000);
    } catch (error) {
      console.error('Failed to load initial context:', error);
    }
  };

  useEffect(() => {
    loadInitialContext();
  }, []);

  const handleCreateDiagram = async (
    prompt: string, 
    model: string, 
    syntax_type: string = 'mermaid', 
    subtype?: string,
    options?: any
  ) => {
    setDiagram({
      loading: true,
      error: undefined,
      code: undefined
    });
    
    const effectiveSubtype = subtype === 'auto' ? undefined : subtype;
    setCurrentSyntax(syntax_type);
    setCurrentType(effectiveSubtype || 'auto');

    try {
      // First switch to workspace screen - this allows the diagram component to be mounted
      // before we try to render the diagram
      setCurrentScreen('workspace');
      
      const response = await diagramService.generateDiagram({
        prompt, // The actual diagram description
        model,
        syntax_type,
        subtype: effectiveSubtype,
        options: options || { agent: { enabled: true } }
      });

      // Now update the diagram data after the component is mounted
      setDiagram({
        loading: false,
        code: response.code,
        error: undefined,
        id: response.id
      });
      
      if (response.id) {
        const iterationResponse = await diagramService.getAgentIterations(response.id);
        setAgentIterations(iterationResponse.current_iteration);
        
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
      
      await logError({ error: errorMessage, details: errorDetails }, 'Generate Diagram');
      
      setDiagram({
        loading: false,
        error: errorMessage
      });
      toast.error(<ErrorToast message={errorMessage} details={errorDetails} />);
    }
  };

  const handleRequestChanges = async (message: string, model: string, updateCurrent: boolean = false) => {
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
      const diagramId = diagram.id || 'current';
      
      // If no diagram.id exists, use generate endpoint instead of update
      const response = await diagramService.requestChanges(
        diagramId,
        message,
        model
      );

      setDiagram(prev => ({
        ...prev,
        loading: false,
        code: response.code,
        error: undefined,
        id: response.id || prev.id
      }));
      
      setAgentIterations(response.current_iteration || 0);
        
      // Refresh the history list after successful diagram update
      if (sidebarRef.current) {
        sidebarRef.current.refreshHistory();
      }
    } catch (err: any) {
      // Extract HTTP status code for Axios errors
      const statusCode = err.response?.status;
      const statusText = err.response?.statusText;
      const statusDisplay = statusCode ? ` (${statusCode}${statusText ? ` ${statusText}` : ''})` : '';
      
      const errorMessage = (err.error || (err.response?.data?.error) || 'Failed to update diagram') + statusDisplay;
      const errorDetails = err.details || err.response?.data || (err.message && { message: err.message });
      
      await logError({ error: errorMessage, details: errorDetails }, 'Update Diagram');
      
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
      const iterationResponse = await diagramService.getAgentIterations(diagramId);
      setAgentIterations(iterationResponse.current_iteration);
      
      toast.success('Diagram loaded from history');
    } catch (err: any) {
      console.error('Failed to load diagram:', err);
      
      // Extract HTTP status code for Axios errors
      const statusCode = err.response?.status;
      const statusText = err.response?.statusText;
      const statusDisplay = statusCode ? ` (${statusCode}${statusText ? ` ${statusText}` : ''})` : '';
      
      const errorMessage = (err.error || (err.response?.data?.error) || 'Failed to load diagram from history') + statusDisplay;
      const errorDetails = err.details || err.response?.data || (err.message && { message: err.message });
      
      await logError({ error: errorMessage, details: errorDetails }, 'Load Diagram');
      
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
    } catch (error: any) {
      const errorMessage = 'Failed to clear logs';
      const errorDetails = {
        message: error.message,
        response: error.response?.data
      };
      await logError({ error: errorMessage, details: errorDetails }, 'Clear Logs');
      toast.error(<ErrorToast message={errorMessage} details={errorDetails} />);
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

  const handleSyntaxChange = (syntax: string) => {
    setCurrentSyntax(syntax);
  };

  const handleTypeChange = (type: string) => {
    setCurrentType(type);
  };

  const handleStartDiagramGeneration = (config: any) => {
    // Track RAG settings
    setRagEnabled(!!config.options?.rag?.enabled);
    if (config.options?.rag?.enabled) {
      setRagDirectory(config.options.rag.api_doc_dir || '');
    }
    
    // Adapt the configuration to match the expected backend format
    handleCreateDiagram(
      config.prompt,
      config.model,
      config.syntax_type,
      config.subtype,
      config.options
    );
  };

  const handleRagDirectoryChange = (directory: string) => {
    setRagDirectory(directory);
  };

  return (
    <ThemeProvider>
      <UIPreferencesProvider>
        <QueryClientProvider client={queryClient}>
          <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
            <CssBaseline />
            
            {currentScreen === 'configuration' && (
              <ConfigurationScreen 
                onStartDiagramGeneration={handleStartDiagramGeneration}
                onSyntaxChange={handleSyntaxChange}
                onTypeChange={handleTypeChange}
              />
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
                onSyntaxChange={handleSyntaxChange}
                onTypeChange={handleTypeChange}
                onCodeChange={(code) => setDiagram(prev => ({ ...prev, code }))}
                syntax={currentSyntax}
                diagramType={currentType}
                ragEnabled={ragEnabled}
                ragDirectory={ragDirectory}
                onRagDirectoryChange={handleRagDirectoryChange}
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
