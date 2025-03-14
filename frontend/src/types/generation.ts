export interface RagConfig {
  enabled: boolean;
  api_doc_dir: string;
}

export interface GenerationOptions {
  rag?: RagConfig;
  agent?: {
    enabled: boolean;
    model_name?: string;
    temperature?: number;
    system_prompt?: string;
    max_iterations?: number;
  };
}

export interface DiagramGenerationRequest {
  description: string;
  model: string;
  syntax: string;
  diagramType?: string;
  options?: GenerationOptions;
}

export interface DiagramGenerationResponse {
  id: string;
  code: string;
  notes: string[];
  valid: boolean;
  iterations: number;
  diagram_id?: string;
  conversation_id?: string;
  current_activity?: string;
}

export interface DiagramValidationError {
  valid: boolean;
  errors: string[];
  suggestions?: string[];
}

export interface ModelInfo {
  id: string;
  name: string;
  provider: string;
  size: number;
  digest: string;
  description?: string;
  parameters?: {
    [key: string]: any;
  };
}

export interface ModelResponse {
  models: ModelInfo[];
}

export interface SyntaxTypes {
  types: {
    [key: string]: string[];
  };
  labels?: {
    [key: string]: string;
  };
}

export interface DiagramModifyRequest {
  message: string;
  model: string;
  updateCurrent?: boolean;
  options?: GenerationOptions;
}

export interface LogEntry {
  timestamp: string;
  level: string;
  type: string;  // Added required type field
  message: string;
  details?: Record<string, any>;
}

export interface AgentIteration {
  iteration: number;
  status: string;
  timestamp: string;
  details?: Record<string, any>;
}

export interface AgentIterationResponse {
  iterations: AgentIteration[];
  total_iterations: number;
  current_iteration: number;
}

export interface Diagram {
  id: string;
  code: string;
  type: string;
  created_at: string;
  updated_at: string;
  metadata?: Record<string, any>;
}

export interface RequestChangesResponse extends DiagramGenerationResponse {
  current_iteration: number;
  total_iterations: number;
}

export interface DiagramHistoryItem {
  id: string;
  description: string;
  syntax: string;
  createdAt: string;
  iterations?: number;
}
