import axios from 'axios';
import { 
  DiagramGenerationRequest, 
  DiagramGenerationResponse, 
  ModelInfo, 
  ModelResponse,
  SyntaxTypes, 
  DiagramModifyRequest,
  LogEntry,
  AgentIteration,
  AgentIterationResponse,
  Diagram,
  RequestChangesResponse,
  DiagramHistoryItem,
} from '../types/generation';

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

interface ErrorResponse {
  error: string;
  details?: string;
}

// Error logging utility
export const logError = (error: any, context?: string): Record<string, any> => {
  const errorMessage = error?.response?.data?.error || error?.message || String(error);
  const errorDetails = {
    message: errorMessage,
    context: context || 'API Error',
    timestamp: new Date().toISOString(),
    type: 'error',  // Added required type field
    details: error?.response?.data || error,
    level: 'error'  // Added for LogEntry compatibility
  };
  console.error(`[${errorDetails.context}]:`, errorDetails);
  return errorDetails;
};

export const diagramService = {
  async generateDiagram(
    request: DiagramGenerationRequest
  ): Promise<DiagramGenerationResponse> {
    try {
      const response = await api.post<DiagramGenerationResponse>('/diagrams/generate', request);
      return response.data;
    } catch (error) {
      throw logError(error, 'Generate Diagram');
    }
  },

  async getAvailableModels(provider: string): Promise<ModelInfo[]> {
    try {
      // The API returns a direct array of models
      const response = await api.get<ModelInfo[]>(`/${provider}/models`);
      return response.data || [];
    } catch (error) {
      console.error('Failed to fetch models:', error);
      throw logError(error, 'Get Models');
    }
  },

  async getSyntaxTypes(): Promise<SyntaxTypes> {
    try {
      const response = await api.get<SyntaxTypes>('/diagrams/syntax-types');
      return response.data;
    } catch (error) {
      throw logError(error, 'Get Syntax Types');
    }
  },

  async validateDiagram(code: string, syntax: string): Promise<{ valid: boolean; errors: string[] }> {
    try {
      const response = await api.post('/diagrams/validate', { code, syntax });
      return response.data;
    } catch (error) {
      throw logError(error, 'Validate Diagram');
    }
  },

  async loadRagContext(directory: string): Promise<{ success: boolean; message: string }> {
    try {
      const response = await api.post('/rag/load', { directory });
      return response.data;
    } catch (error) {
      throw logError(error, 'Load RAG Context');
    }
  },

  async requestChanges(diagramId: string, changes: string, model: string, syntax: string = 'mermaid'): Promise<RequestChangesResponse> {
    try {
      const response = await api.post<RequestChangesResponse>(`/diagrams/diagram/${diagramId}/update`, {
        prompt: changes,  // Changed from 'changes' to 'prompt' to match backend expectation
        model,
        syntax_type: syntax,  // Use the provided syntax type instead of hardcoding to 'mermaid'
        options: {
          agent: {
            enabled: true,
            max_iterations: 3,
            model_name: model  // Include model in the agent options structure
          }
        }
      });
      return response.data;
    } catch (error) {
      throw logError(error, 'Request Changes');
    }
  },

  async getAgentIterations(diagramId: string): Promise<{ iterations: AgentIteration[]; current_iteration: number }> {
    try {
      const response = await api.get<AgentIterationResponse>(`/diagrams/diagram/${diagramId}/iterations`);
      return {
        iterations: response.data.iterations,
        current_iteration: response.data.current_iteration
      };
    } catch (error) {
      throw logError(error, 'Get Agent Iterations');
    }
  },

  async getDiagramById(diagramId: string): Promise<Diagram> {
    try {
      const response = await api.get<Diagram>(`/diagrams/diagram/${diagramId}`);
      return response.data;
    } catch (error) {
      throw logError(error, 'Get Diagram');
    }
  },

  async clearLogs(): Promise<void> {
    try {
      await api.post('/logs/clear');
    } catch (error) {
      throw logError(error, 'Clear Logs');
    }
  },

  async getLogs(): Promise<LogEntry[]> {
    try {
      const response = await api.get<{ logs: LogEntry[] }>('/logs');
      // Handle case where response.data.logs is undefined
      if (!response.data || !Array.isArray(response.data.logs)) {
        return [];  // Return empty array if no logs
      }
      return response.data.logs.map(log => ({
        ...log,
        type: log.type || 'system'  // Ensure type field is present
      }));
    } catch (error) {
      // Instead of throwing, return an empty array with the error logged
      console.error('Failed to fetch logs:', error);
      return [];
    }
  },

  async getDiagramHistory(): Promise<DiagramHistoryItem[]> {
    try {
      const response = await api.get<DiagramHistoryItem[]>('/diagrams/history');
      return response.data;
    } catch (error) {
      throw logError(error, 'Get Diagram History');
    }
  },

  async deleteDiagram(diagramId: string): Promise<{ status: string; message: string }> {
    try {
      const response = await api.delete<{ status: string; message: string }>(`/diagrams/diagram/${diagramId}`);
      return response.data;
    } catch (error) {
      throw logError(error, 'Delete Diagram');
    }
  },

  async clearHistory(): Promise<{ status: string; message: string; state: { diagrams_deleted: number; success: boolean } }> {
    try {
      const response = await api.delete<{ 
        status: string; 
        message: string;
        state: {
          diagrams_deleted: number;
          success: boolean;
          error?: string;
        }
      }>('/diagrams/clear');
      return response.data;
    } catch (error) {
      throw logError(error, 'Clear Diagram History');
    }
  },
};
