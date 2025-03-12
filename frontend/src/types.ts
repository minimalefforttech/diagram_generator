export interface LogEntry {
  type: 'error' | 'llm' | 'info';
  message: string;
  timestamp: string;
  details?: any;
}

export interface DiagramState {
  id?: string;
  code?: string;
  loading: boolean;
  error?: string;
}

export interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}
