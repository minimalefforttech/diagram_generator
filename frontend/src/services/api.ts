import axios, { AxiosInstance } from 'axios';

export interface DiagramGenerationOptions {
    model?: string;
    agent?: {
        enabled: boolean;
        max_iterations?: number;
        temperature?: number;
    };
    rag?: {
        enabled: boolean;
        api_doc_dir?: string;
    };
}

export interface DiagramRequest {
    description: string;
    syntax_type?: string;  // mermaid, plantuml
    subtype?: string;      // flowchart, sequence, etc
    model?: string;
    options?: DiagramGenerationOptions;
}

export interface DiagramResponse {
    code: string;
    type: string;
    subtype: string;
    notes: string[];
}

export interface SyntaxTypesResponse {
    syntax: string[];
    types: {
        [key: string]: string[];
    };
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

export interface ModelInfo {
    id: string;
    name: string;
    provider: string;
    size: number;
    digest: string;
}

const log = (message: string, details?: any) => {
    console.log(`[API] ${message}`, details);
};

const api: AxiosInstance = axios.create({
    baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
});

// Add a simple handler to log any API errors
const handleError = (error: any) => {
    if (error instanceof axios.AxiosError) {
        console.error('Failed API request:', error);
    } else {
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

export const diagramService = {
    baseUrl: api.defaults.baseURL,

    async generateDiagram(request: DiagramRequest): Promise<DiagramResponse> {
        try {
            const response = await api.post<DiagramResponse>(
                '/diagrams/generate',
                request
            );
            return response.data;
        } catch (error) {
            handleError(error);
            throw error;
        }
    },

    async getSyntaxTypes(): Promise<SyntaxTypesResponse> {
        try {
            const response = await api.get<SyntaxTypesResponse>(
                '/diagrams/syntax-types'
            );
            return response.data;
        } catch (error) {
            handleError(error);
            throw error;
        }
    },

    async getAvailableModels(service: string): Promise<ModelInfo[]> {
        try {
            const response = await api.get<ModelInfo[]>(`/${service}/models`);
            return response.data;
        } catch (error) {
            handleError(error);
            throw error;
        }
    },

    async getDiagramById(id: string): Promise<DiagramResponse> {
        try {
            const response = await api.get<DiagramResponse>(`/diagrams/${id}`);
            return response.data;
        } catch (error) {
            handleError(error);
            throw error;
        }
    },

    async getAgentIterations(id: string): Promise<number> {
        try {
            const response = await api.get<number>(`/diagrams/${id}/iterations`);
            return response.data;
        } catch (error) {
            handleError(error);
            throw error;
        }
    },

    async requestChanges(id: string, request: DiagramRequest): Promise<DiagramResponse> {
        try {
            const response = await api.post<DiagramResponse>(
                `/diagrams/${id}/changes`,
                request
            );
            return response.data;
        } catch (error) {
            handleError(error);
            throw error;
        }
    },

    async getLogs(): Promise<LogEntry[]> {
        try {
            const response = await api.get<LogEntry[]>('/logs');
            return response.data;
        } catch (error) {
            handleError(error);
            throw error;
        }
    },

    async clearLogs(): Promise<void> {
        try {
            await api.delete('/logs');
        } catch (error) {
            handleError(error);
            throw error;
        }
    }
};
