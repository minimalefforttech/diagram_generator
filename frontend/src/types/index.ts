export interface DiagramState {
    loading: boolean;
    code?: string;
    error?: string;
    id?: string;
}

export interface DiagramRequest {
    description: string;
    model?: string;
    syntax?: string;
    diagramType?: string;
    options?: Record<string, any>;
    previousDiagramId?: string;
}

export interface DiagramResponse {
    code: string;
    type: string;
    subtype?: string;
    notes?: string[];
    id?: string;
}

export interface LogEntry {
    timestamp: string;
    level: string;
    message: string;
    details?: Record<string, any>;
}

export interface SyntaxTypesResponse {
    syntax: string[];
    types: Record<string, string[]>;
}

export interface ModelInfo {
    name: string;
    size?: string;
    family?: string;
    quantized?: boolean;
    parameters?: string;
}

export interface DiagramHistoryItem {
    id: string;
    description: string;
    syntax: string;
    createdAt: string;
    iterations?: number;
}