import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
});

export interface Model {
  id: string;
  name: string;
  provider: string;
}

export interface GenerateDiagramRequest {
  description: string;
  type?: string;
  model?: string;
  options?: {
    agent?: {
      enabled?: boolean;
      maxIterations?: number;
    };
    enabled?: boolean;
  };
}

export interface GenerateDiagramResponse {
  type: string;
  diagram: string;
  code?: string;
  notes: string[];
}

export interface LogEntry {
  type: 'error' | 'llm' | 'info';
  message: string;
  timestamp: string;
  details?: any;
}

export interface DiagramApiError {
  error: string;
  details?: any;
}

// Utility function to extract clean diagram code from potentially verbose LLM responses
function extractDiagramCode(rawResponse: string): string {
  // Case 1: Check for mermaid code block syntax
  const mermaidBlockRegex = /```mermaid\n([\s\S]*?)```/;
  const mermaidMatch = mermaidBlockRegex.exec(rawResponse);
  if (mermaidMatch && mermaidMatch[1]) {
    return mermaidMatch[1].trim();
  }

  // Case 2: Look for explicit diagram syntax markers
  const graphLines = rawResponse.split('\n').filter(line => 
    line.trim().startsWith('graph TD') || 
    line.trim().startsWith('graph LR') || 
    line.trim().startsWith('flowchart ') || 
    line.trim().startsWith('sequenceDiagram') ||
    line.trim().startsWith('classDiagram')
  );
  
  if (graphLines.length > 0) {
    // Find the line that starts a diagram
    const startIndex = rawResponse.indexOf(graphLines[0]);
    if (startIndex >= 0) {
      const possibleDiagram = rawResponse.substring(startIndex);
      const lines = possibleDiagram.split('\n');
      const diagramLines = [];
      
      // Extract lines until we find something that looks like explanatory text
      for (const line of lines) {
        const lowerLine = line.toLowerCase().trim();
        // Stop when we hit explanatory text or descriptive elements
        if (lowerLine === '' ||
            lowerLine.startsWith('this diagram') ||
            lowerLine.startsWith('description:') || 
            lowerLine.startsWith('here is') ||
            lowerLine.startsWith('the diagram') ||
            lowerLine.startsWith('this shows')) {
          break;
        }
        diagramLines.push(line);
      }
      
      return diagramLines.join('\n').trim();
    }
  }
  
  // Case 3: If the response has a clear structure with diagram code followed by text
  // Try to identify where the diagram code ends and explanatory text begins
  const lines = rawResponse.trim().split('\n');
  const diagramLines = [];
  let foundExplanatoryText = false;
  
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim();
    const lowerLine = line.toLowerCase();
    
    // Check if this line looks like the start of explanatory text
    if (i > 0 && (
        lowerLine.startsWith('this diagram') || 
        lowerLine.startsWith('this shows') ||
        lowerLine.startsWith('the diagram') ||
        lowerLine.startsWith('description:') ||
        lowerLine.startsWith('here is'))) {
      foundExplanatoryText = true;
      break;
    }
    
    // If we find an empty line after some content, and the next non-empty line 
    // starts with lowercase or is a sentence, assume we've hit explanatory text
    if (line === '' && diagramLines.length > 0 && i < lines.length - 1) {
      const nextLine = lines.slice(i + 1).find(l => l.trim() !== '');
      if (nextLine && 
          (nextLine.trim()[0] === nextLine.trim()[0].toLowerCase() && 
           nextLine.trim()[0] !== nextLine.trim()[0].toUpperCase() || // First character is lowercase
           /^[A-Z][a-z]/.test(nextLine.trim()))) { // Looks like a sentence (capital followed by lowercase)
        foundExplanatoryText = true;
        break;
      }
    }
    
    diagramLines.push(lines[i]);
  }
  
  if (foundExplanatoryText && diagramLines.length > 0) {
    // Remove any trailing empty lines
    while (diagramLines.length > 0 && diagramLines[diagramLines.length - 1].trim() === '') {
      diagramLines.pop();
    }
    return diagramLines.join('\n');
  }
  
  // If all else fails, return the raw response as-is
  return rawResponse.trim();
}

export const diagramService = {
  async generateDiagram(request: GenerateDiagramRequest): Promise<GenerateDiagramResponse> {
    try {
      const response = await api.post('/diagrams/generate', request);
      
      // Process response to handle verbose LLM responses
      if (response.data && response.data.diagram) {
        response.data.diagram = extractDiagramCode(response.data.diagram);
      }
      
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        throw {
          error: error.response.data.error || 'Failed to generate diagram',
          details: error.response.data
        };
      }
      throw {
        error: 'Failed to connect to the server',
        details: error
      };
    }
  },

  async requestChanges(diagramId: string, request: GenerateDiagramRequest): Promise<GenerateDiagramResponse> {
    try {
      const response = await api.post(`/diagrams/${diagramId}/changes`, request);
      
      // Process response to handle verbose LLM responses
      if (response.data && response.data.diagram) {
        response.data.diagram = extractDiagramCode(response.data.diagram);
      }
      
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        throw {
          error: error.response.data.error || 'Failed to update diagram',
          details: error.response.data
        };
      }
      throw {
        error: 'Failed to connect to the server',
        details: error
      };
    }
  },

  async getLogs(): Promise<LogEntry[]> {
    try {
      const response = await api.get('/logs');
      return response.data;
    } catch (error) {
      console.error('Failed to fetch logs:', error);
      return [];
    }
  },

  async log(entry: Omit<LogEntry, 'timestamp'>): Promise<void> {
    try {
      await api.post('/logs', entry);
    } catch (error) {
      console.error('Failed to log entry:', error);
    }
  },

  async getAvailableModels(): Promise<Model[]> {
    try {
      const response = await api.get('/ollama/models');
      return response.data;
    } catch (error) {
      console.error('Failed to fetch models:', error);
      throw error;
    }
  },

  async checkHealth(): Promise<boolean> {
    try {
      const response = await api.get('/health');
      return response.data.status === 'healthy';
    } catch (error) {
      return false;
    }
  }
};

// Add interceptors to handle raw LLM communication logging
api.interceptors.request.use(async (config) => {
  if (config.url?.includes('/diagrams/')) {
    await diagramService.log({
      type: 'llm',
      message: 'LLM Request',
      details: {
        url: config.url,
        method: config.method,
        data: config.data
      }
    });
  }
  return config;
});

api.interceptors.response.use(
  async (response) => {
    if (response.config.url?.includes('/diagrams/')) {
      await diagramService.log({
        type: 'llm',
        message: 'LLM Response',
        details: {
          url: response.config.url,
          status: response.status,
          data: response.data
        }
      });
    }
    return response;
  },
  async (error) => {
    if (error.config?.url?.includes('/diagrams/')) {
      await diagramService.log({
        type: 'error',
        message: 'API Error',
        details: {
          url: error.config.url,
          error: error.message,
          response: error.response?.data
        }
      });
    }
    throw error;
  }
);
