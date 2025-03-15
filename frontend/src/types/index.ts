import { AgentConfig } from './configs';

export interface DiagramState {
  loading: boolean;
  code?: string;
  error?: string;
  id?: string;
}

// Must match backend LogEntry
export interface LogEntry {
  timestamp: string;
  level: string;
  type: string;
  message: string;
  details?: Record<string, any>;
}

export interface GenerationOptions {
  agent?: AgentConfig;
  rag?: {
    enabled: boolean;
    api_doc_dir: string;
  };
}

// Diagram types & syntax
export const DIAGRAM_TYPES = {
  graph: 'Graph',
  sequence: 'Sequence',
  class: 'Class',
  state: 'State',
  er: 'Entity Relationship',
  gantt: 'Gantt',
  pie: 'Pie',
  flowchart: 'Flowchart',
  mindmap: 'Mind Map',
  timeline: 'Timeline',
} as const;

export const DIAGRAM_SYNTAX = {
  mermaid: 'Mermaid',
  plantuml: 'PlantUML',
} as const;

export type DiagramType = keyof typeof DIAGRAM_TYPES;
export type DiagramSyntax = keyof typeof DIAGRAM_SYNTAX;
