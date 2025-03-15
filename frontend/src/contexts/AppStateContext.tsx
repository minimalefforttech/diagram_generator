import React, { createContext, useContext, useState, useEffect } from 'react';
import { DiagramState, LogEntry } from '../types';

// Define the shape of our global application state
interface AppState {
  diagram: DiagramState;
  logs: LogEntry[];
  agentIterations: number;
  currentSyntax: string;
  currentType: string;
  preferredModel: string;
  recentDiagrams: string[];
}

// Define the context value shape
interface AppStateContextValue {
  state: AppState;
  updateDiagram: (diagram: DiagramState) => void;
  updateLogs: (logs: LogEntry[]) => void;
  updateAgentIterations: (iterations: number) => void;
  updateSyntax: (syntax: string) => void;
  updateType: (type: string) => void;
  setPreferredModel: (model: string) => void;
  addRecentDiagram: (diagramId: string) => void;
  resetState: () => void;
}

// Initial state
const initialState: AppState = {
  diagram: { loading: false },
  logs: [],
  agentIterations: 0,
  currentSyntax: 'mermaid',
  currentType: 'auto',
  preferredModel: '',
  recentDiagrams: []
};

// Create context
const AppStateContext = createContext<AppStateContextValue | undefined>(undefined);

// Custom hook to use the app state context
export const useAppState = () => {
  const context = useContext(AppStateContext);
  if (context === undefined) {
    throw new Error('useAppState must be used within an AppStateProvider');
  }
  return context;
};

// Storage key for persisting state in localStorage
const APP_STATE_STORAGE_KEY = 'diagramGeneratorAppState';

// Provider component
export const AppStateProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  // Load state from localStorage or use initial state
  const [state, setState] = useState<AppState>(() => {
    try {
      const storedState = localStorage.getItem(APP_STATE_STORAGE_KEY);
      return storedState ? JSON.parse(storedState) : initialState;
    } catch (error) {
      console.error('Failed to parse stored app state:', error);
      return initialState;
    }
  });

  // Save state to localStorage whenever it changes
  useEffect(() => {
    try {
      localStorage.setItem(APP_STATE_STORAGE_KEY, JSON.stringify(state));
    } catch (error) {
      console.error('Failed to save app state to localStorage:', error);
    }
  }, [state]);

  // Update functions
  const updateDiagram = (diagram: DiagramState) => {
    setState(prev => ({ ...prev, diagram }));
  };

  const updateLogs = (logs: LogEntry[]) => {
    setState(prev => ({ ...prev, logs }));
  };

  const updateAgentIterations = (iterations: number) => {
    setState(prev => ({ ...prev, agentIterations: iterations }));
  };

  const updateSyntax = (syntax: string) => {
    setState(prev => ({ ...prev, currentSyntax: syntax.toLowerCase() }));
  };

  const updateType = (type: string) => {
    setState(prev => ({ ...prev, currentType: type }));
  };

  const setPreferredModel = (model: string) => {
    setState(prev => ({ ...prev, preferredModel: model }));
  };

  const addRecentDiagram = (diagramId: string) => {
    setState(prev => {
      // Add to front of array and remove duplicates
      const filteredRecent = prev.recentDiagrams.filter(id => id !== diagramId);
      return { 
        ...prev, 
        recentDiagrams: [diagramId, ...filteredRecent].slice(0, 10) // Keep max 10 recent diagrams
      };
    });
  };

  const resetState = () => {
    // Keep only certain values like preferredModel when resetting
    setState(prev => ({
      ...initialState,
      preferredModel: prev.preferredModel,
      recentDiagrams: prev.recentDiagrams
    }));
  };

  // Context value
  const value: AppStateContextValue = {
    state,
    updateDiagram,
    updateLogs,
    updateAgentIterations,
    updateSyntax,
    updateType,
    setPreferredModel,
    addRecentDiagram,
    resetState
  };

  return (
    <AppStateContext.Provider value={value}>
      {children}
    </AppStateContext.Provider>
  );
};

export default AppStateProvider;