import axios, { AxiosInstance } from 'axios';
import { 
    DiagramRequest, 
    DiagramResponse, 
    LogEntry, 
    SyntaxTypesResponse,
    ModelInfo,
    DiagramHistoryItem
} from '../types';

const log = (message: string, details?: any) => {
    console.log(`[API] ${message}`, details);
};

const api: AxiosInstance = axios.create({
    baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
    headers: {
        'Content-Type': 'application/json',
    }
});

// Log error to backend logging system
export const logError = async (message: string, details?: any) => {
  try {
    await api.post('/logs', {
      type: 'error',
      message,
      details
    });
  } catch (e) {
    console.error('Failed to log error:', e);
  }
};

// Add a handler to log any API errors
const handleError = async (error: any) => {
    if (error instanceof axios.AxiosError) {
        const errorDetails = {
            url: error.config?.url,
            method: error.config?.method,
            status: error.response?.status,
            statusText: error.response?.statusText,
            data: error.response?.data,
            message: error.message
        };
        await logError('Failed API request', errorDetails);
        console.error('Failed API request:', error);
    } else {
        await logError('Unexpected error', { message: error.message });
        console.error('Unexpected error:', error);
    }
};

api.interceptors.request.use((req) => {
    if (req.url?.includes('/diagrams/')) {
        log('HTTP request', req.data);
    }
    return req;
});

api.interceptors.response.use((res) => {
    log('HTTP response', res.data);
    return res;
});

// --------------------------------------------------------------------------
// API functions & methods
// --------------------------------------------------------------------------

// API service for diagram generation and management
export const diagramService = {
  // Generate a new diagram
  generateDiagram: async (request: DiagramRequest): Promise<DiagramResponse> => {
    try {
      const payload = {
        description: request.description,
        syntax_type: request.syntax,
        subtype: request.diagramType || 'auto',
        model: request.model,
        options: request.options
      };
      const response = await api.post('/diagrams/generate', payload);
      return response.data;
    } catch (error) {
      handleError(error);
      throw error;
    }
  },

  async requestChanges(id: string | undefined, request: DiagramRequest, updateCurrent: boolean = false): Promise<DiagramResponse> {
    try {
        // If no ID or updateCurrent is false, use generate endpoint
        const endpoint = id && updateCurrent ? `/diagrams/diagram/${id}/update` : '/diagrams/generate';
        const payload: any = {
            description: request.description,
            syntax_type: request.syntax,
            subtype: request.diagramType || 'auto',
            model: request.model,
            options: request.options
        };
        // Only include previousDiagramId if we have an ID but aren't updating
        if (id && !updateCurrent) {
            payload.previousDiagramId = id;
        }
        
        const response = await api.post<DiagramResponse>(endpoint, payload);
        return response.data;
    } catch (error) {
        handleError(error);
        throw error;
    }
  },

  // Get available syntax types and subtypes
  getSyntaxTypes: async (): Promise<SyntaxTypesResponse> => {
    try {
      const response = await api.get('/diagrams/syntax-types');
      return response.data;
    } catch (error) {
      handleError(error);
      // Return default types if API fails
      return {
        syntax: ['mermaid', 'plantuml'],
        types: {
          mermaid: ['flowchart', 'sequence', 'class', 'state', 'er', 'gantt', 'pie', 'mindmap'],
          plantuml: ['sequence', 'class', 'activity', 'component', 'state', 'mindmap', 'gantt']
        }
      };
    }
  },

  // Convert diagram between types
  convertDiagram: async (code: string, fromType: string, toType: string) => {
    try {
      const response = await api.post('/diagrams/convert', {
        code,
        from_type: fromType,
        to_type: toType
      });
      return response.data;
    } catch (error) {
      handleError(error);
      throw error;
    }
  },

  // Validate diagram syntax
  validateDiagram: async (code: string, syntaxType: string) => {
    try {
      const response = await api.post('/diagrams/validate', {
        code,
        syntax_type: syntaxType
      });
      return response.data;
    } catch (error) {
      handleError(error);
      throw error;
    }
  },

  // Get diagram history
  getDiagramHistory: async () => {
    try {
      const response = await api.get('/diagrams/history');
      return response.data;
    } catch (error) {
      handleError(error);
      throw error;
    }
  },

  // Get logs
  getLogs: async () => {
    try {
      const response = await api.get('/logs');
      return response.data;
    } catch (error) {
      handleError(error);
      return []; // Return empty array on error
    }
  },

  // Get a specific diagram by ID
  getDiagramById: async (id: string) => {
    try {
      const response = await api.get(`/diagrams/diagram/${id}`);
      return response.data;
    } catch (error) {
      handleError(error);
      throw error;
    }
  },

  // Delete a specific diagram
  deleteDiagram: async (id: string) => {
    try {
      const response = await api.delete(`/diagrams/diagram/${id}`);
      return response.data;
    } catch (error) {
      handleError(error);
      throw error;
    }
  },

  // Clear all diagram history
  clearHistory: async () => {
    try {
      const response = await api.delete('/diagrams/clear');
      return response.data;
    } catch (error) {
      handleError(error);
      throw error;
    }
  },

  // Clear logs
  clearLogs: async () => {
    try {
      const response = await api.delete('/logs');
      return response.data;
    } catch (error) {
      handleError(error);
      throw error;
    }
  },

  // Get agent iterations for a diagram
  getAgentIterations: async (diagramId: string) => {
    try {
      const response = await api.get(`/diagrams/diagram/${diagramId}/iterations`);
      return response.data;
    } catch (error) {
      handleError(error);
      return 0; // Return 0 iterations on error
    }
  },

  // Get available models
  getAvailableModels: async (service: string = 'ollama') => {
    try {
      const response = await api.get(`/${service}/models`);
      return response.data;
    } catch (error) {
      handleError(error);
      // Return default model on error
      return [{
        id: 'llama2:latest',
        name: 'llama2:latest',
        provider: service,
        size: 0,
        digest: ''
      }];
    }
  }
};
