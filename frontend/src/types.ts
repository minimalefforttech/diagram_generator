export interface DiagramState {
  loading: boolean;
  code?: string;
  error?: string;
  id?: string;
}

export interface LogEntry {
  timestamp: string;
  type: string;
  message: string;
  details?: any;
}

export interface DiagramGenerationOptions {
  agent?: {
    enabled: boolean;
    maxIterations?: number;
  };
  rag?: {
    enabled: boolean;
    apiDocDir?: string;
  };
}

export interface DiagramRequest {
  prompt: string;
  description?: string;
  model?: string;
  syntax?: string;
  diagramType?: string;
  options?: DiagramGenerationOptions;
}

export interface DiagramResponse {
  id?: string;
  code: string;
  type?: string;
  description?: string;
  prompt: string;
  notes?: string[];
}

export interface SyntaxTypesResponse {
  syntax: string[];
  types: {
    [key: string]: string[];
  };
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
