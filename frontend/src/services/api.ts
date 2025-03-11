import axios from 'axios';
import type { AxiosInstance, AxiosResponse } from 'axios';

export interface ValidationResponse {
  valid: boolean;
  errors: string[];
  suggestions: string[];
}

export interface ConversionResponse {
  diagram: string;
  source_type: string;
  target_type: string;
  notes: string[];
}

const api: AxiosInstance = axios.create({
  baseURL: 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface DiagramGenerationRequest {
  description: string;
  diagram_type?: 'mermaid' | 'plantuml' | 'c4';
  options?: {
    agent?: {
      enabled?: boolean;
      max_iterations?: number;
    };
    rag?: {
      enabled?: boolean;
      api_doc_dir?: string;
    };
  };
}

export interface DiagramGenerationResponse {
  diagram: string;
  type: string;
  notes: string[];
}

export interface ConversationCreateRequest {
  diagram_id: string;
  message: string;
}

export interface ConversationMessage {
  role: string;
  content: string;
  timestamp: string;
  metadata: Record<string, any>;
}

export interface ConversationResponse {
  id: string;
  diagram_id: string;
  messages: ConversationMessage[];
  created_at: string;
  updated_at: string;
  metadata: Record<string, any>;
}

export const diagramService = {
  generate: async (request: DiagramGenerationRequest): Promise<DiagramGenerationResponse> => {
    const { description, diagram_type = 'mermaid', options } = request;
    const response: AxiosResponse<DiagramGenerationResponse> = await api.post('/diagrams/generate', {
      description,
      diagram_type,
      options,
    });
    return response.data;
  },

  validate: async (code: string, diagram_type: string = 'mermaid'): Promise<ValidationResponse> => {
    const response: AxiosResponse<ValidationResponse> = await api.post('/diagrams/validate', {
      code,
      diagram_type,
    });
    return response.data;
  },

  convert: async (diagram: string, source_type: string, target_type: string): Promise<ConversionResponse> => {
    const response: AxiosResponse<ConversionResponse> = await api.post('/diagrams/convert', {
      diagram,
      source_type,
      target_type,
    });
    return response.data;
  },

  createConversation: async (request: ConversationCreateRequest): Promise<ConversationResponse> => {
    const response: AxiosResponse<ConversationResponse> = await api.post('/diagrams/conversations', request);
    return response.data;
  },

  getConversation: async (id: string): Promise<ConversationResponse> => {
    const response: AxiosResponse<ConversationResponse> = await api.get(`/diagrams/conversations/${id}`);
    return response.data;
  },

  listConversations: async (diagram_id: string): Promise<ConversationResponse[]> => {
    const response: AxiosResponse<ConversationResponse[]> = await api.get(`/diagrams/conversations?diagram_id=${diagram_id}`);
    return response.data;
  },

  continueConversation: async (id: string, message: string): Promise<ConversationResponse> => {
    const response: AxiosResponse<ConversationResponse> = await api.post(`/diagrams/conversations/${id}/continue`, {
      message,
    });
    return response.data;
  },

  deleteConversation: async (id: string): Promise<void> => {
    await api.delete(`/diagrams/conversations/${id}`);
  },
};

// Error handling interceptor
api.interceptors.response.use(
  (response: AxiosResponse) => response,
  (error: {
    response?: {
      data: { detail?: string };
      status: number;
    };
    request?: any;
    message?: string;
  }) => {
    if (error.response) {
      // Server responded with error status
      const message = error.response.data.detail || 'An error occurred';
      console.error('API Error:', message);
      throw new Error(message);
    } else if (error.request) {
      // Request made but no response
      console.error('Network Error:', error);
      throw new Error('Network error. Please check your connection.');
    } else {
      // Error setting up request
      console.error('Request Error:', error);
      throw new Error('Error setting up request.');
    }
  }
);
