export interface AgentConfig {
  enabled: boolean;
  model_name?: string;
  temperature?: number;
  system_prompt?: string;
  max_iterations?: number;
}

export interface RagConfig {
  enabled: boolean;
  api_doc_dir: string;
  chunk_size?: number;
  chunk_overlap?: number;
  embeddings_model?: string;
  similarity_top_k?: number;
}

export interface DiagramGenerationOptions {
  agent?: AgentConfig;
  rag?: RagConfig;
}

export interface UIPreferences {
  theme: 'light' | 'dark';
  codeEditorVisible: boolean;
  sidebarVisible: boolean;
  logsVisible: boolean;
  fontSize: number;
  diagramZoom: number;
}

export interface GlobalSettings {
  apiUrl: string;
  defaultModel: string;
  defaultSyntax: string;
  pollInterval: number;
  retryAttempts: number;
  retryDelay: number;
}

export interface ModelConfig {
  name: string;
  provider: string;
  size: number;
  description?: string;
  parameters?: Record<string, any>;
}
