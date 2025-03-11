# Architecture Documentation

This document provides an overview of the core components and how they interact to deliver diagram generation, validation, and conversion services.

## System Architecture

### Components Overview

```mermaid
graph TB
    API[FastAPI Routes]
    DG[DiagramGenerator]
    OS[OllamaService]
    LLM[Local Ollama LLM]
    Cache[(Request Cache)]

    API --> DG
    DG --> OS
    OS --> LLM
    OS --> Cache
```

The system consists of three main layers:

1. **API Layer** (`backend/api/diagrams.py`)
   - FastAPI endpoints for diagram operations
   - Request/response handling
   - Input validation
   - Error handling

2. **Core Layer** (`backend/core/diagram_generator.py`)
   - Diagram generation logic
   - Prompt construction
   - Response processing
   - Validation orchestration

3. **Service Layer** (`backend/services/ollama.py`)
   - LLM communication
   - Response caching
   - Error handling
   - Response validation

### Component Details

#### FastAPI Routes
- Handles HTTP requests and responses
- Routes:
  - `/diagrams/generate`
  - `/diagrams/validate`
  - `/diagrams/convert`
- Input validation using FastAPI's type system
- Error handling with proper HTTP status codes

#### DiagramGenerator
- Central business logic component
- Responsibilities:
  - Building LLM prompts
  - Processing LLM responses
  - Extracting diagram code
  - Post-processing and cleanup
  - Validation orchestration

#### OllamaService
- LLM integration layer
- Features:
  - Request caching
  - Connection management
  - Response validation
  - Error handling

## Request Flow

### Diagram Generation Flow

```mermaid
sequenceDiagram
    participant Client
    participant API as FastAPI
    participant DG as DiagramGenerator
    participant OS as OllamaService
    participant LLM as Ollama LLM

    Client->>API: POST /diagrams/generate
    Note over API: Validate request params
    API->>DG: generate_diagram()
    
    DG->>DG: Create prompt
    DG->>OS: generate_completion()
    
    alt Cache Hit
        OS->>OS: Return cached response
    else Cache Miss
        OS->>LLM: Send prompt
        LLM-->>OS: Return response
        OS->>OS: Cache response
    end
    
    OS-->>DG: Return completion
    DG->>DG: Process response
    DG->>DG: Validate diagram
    DG-->>API: Return result
    API-->>Client: JSON response
```

### Error Handling Flow

```mermaid
graph TD
    A[Client Request] --> B{Input Valid?}
    B -->|No| C[Return 400]
    B -->|Yes| D{LLM Available?}
    D -->|No| E[Return 503]
    D -->|Yes| F{Generation Success?}
    F -->|No| G[Return 500]
    F -->|Yes| H{Validation Pass?}
    H -->|No| I[Return with Warnings]
    H -->|Yes| J[Return Success]
```

## Key Design Decisions

1. **Async Operations**
   - All operations are async for better performance
   - Allows handling multiple requests efficiently

2. **Caching Strategy**
   - Uses `requests_cache` for LLM responses
   - Configurable cache duration
   - Improves response times for repeated requests

3. **Error Handling**
   - Graceful degradation
   - Detailed error messages
   - Proper HTTP status codes

4. **Response Processing**
   - Markdown extraction
   - Code formatting
   - Validation checks

## Testing Strategy

1. **Unit Tests**
   - Individual component testing
   - Mock LLM responses
   - Error case coverage

2. **Integration Tests**
   - API endpoint testing
   - End-to-end flows
   - Error handling verification

3. **Test Coverage**
   - Core business logic
   - API endpoints
   - Service layer

## Future Considerations

1. **Scalability**
   - Load balancing
   - Multiple LLM instances
   - Distributed caching

2. **Security**
   - Authentication
   - Rate limiting
   - Input sanitization

3. **Monitoring**
   - Performance metrics
   - Error tracking
   - Usage statistics

4. **Extensions**
   - Additional diagram types
   - Custom validation rules
   - Collaborative features
