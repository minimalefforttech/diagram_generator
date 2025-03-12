export interface DiagramState {
  loading: boolean;
  error?: string;
  code?: string;
  id?: string;
}

export interface LogEntry {
  type: 'error' | 'llm' | 'info' | string;
  message: string;
  timestamp: string;
  details?: any;
}

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
  model?: string;
  syntax?: string;
  syntax_type?: string;  // mermaid, plantuml
  diagramType?: string;
  subtype?: string;      // flowchart, sequence, etc
  options?: DiagramGenerationOptions;
}

export interface DiagramResponse {
  code: string;
  id?: string;
  type?: string;
  subtype?: string;
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
