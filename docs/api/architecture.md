# Architecture Documentation

This document provides an overview of the core components and how they interact to generate, validate, and manage diagrams.

## System Architecture

### Components Overview

```mermaid
graph TB
    subgraph Frontend["Frontend (React)"]
        UI[UI Components]
        History[History Management]
        State[State Management]
    end

    subgraph API["API Layer (FastAPI)"]
        Routes[API Routes]
        Models[Data Models]
        Storage[Storage Handler]
    end

    subgraph Agent["Diagram Agent"]
        Tools[Tool Set]
        LLMHandler[LLM Handler]
        Validator[Diagram Validator]
        RAG[RAG Provider]
    end

    subgraph External["External Services"]
        Ollama[Ollama LLM]
        DB[(SQLite DB)]
    end

    UI --> Routes
    History --> Storage
    Routes --> Agent
    Agent --> Ollama
    Agent --> RAG
    Storage --> DB
    RAG --> Ollama
```

The system consists of four main layers:

1. **Frontend Layer** (`frontend/src/`)
   - React components for user interaction
   - State management with contexts
   - History tracking and versioning
   - Real-time diagram preview

2. **API Layer** (`backend/api/`)
   - FastAPI endpoints for operations
   - Data models and validation
   - Storage management
   - Error handling

3. **Agent Layer** (`backend/agents/`)
   - Tool-based diagram generation
   - Validation and iteration
   - RAG integration
   - LLM prompt management

4. **Storage Layer** (`backend/storage/`)
   - SQLite database integration
   - History persistence
   - Version tracking
   - Metadata management

### Component Details

#### DiagramAgent

The core component using a tool-based approach:

```mermaid
classDiagram
    class DiagramAgent {
        +generate_diagram()
        +update_diagram()
        +run_agent()
        -determine_requirements()
        -generate_with_llm()
        -validate()
        -strip_comments()
        -fix_diagram()
    }
    
    class DiagramAgentState {
        +description: str
        +diagram_type: DiagramType
        +code: Optional[str]
        +validation_result: Dict
        +errors: List[str]
        +iterations: int
        +context_section: str
        +notes: List[str]
    }
    
    class Tools {
        +validate_mermaid()
        +validate_plantuml()
        +strip_comments()
        +detect_diagram_type()
    }
    
    DiagramAgent -- DiagramAgentState
    DiagramAgent -- Tools
```

#### RAG Integration

```mermaid
sequenceDiagram
    participant UI as Frontend
    participant API as API Layer
    participant Agent as DiagramAgent
    participant RAG as RAG Provider
    participant LLM as Ollama LLM

    UI->>API: Generate diagram with code context
    API->>Agent: generate_diagram(context_dir)
    Agent->>RAG: load_docs_from_directory()
    RAG-->>Agent: Success
    Agent->>RAG: get_relevant_context(query)
    RAG->>LLM: Generate embeddings
    LLM-->>RAG: Embeddings
    RAG-->>Agent: Relevant code context
    Agent->>LLM: Generate diagram with context
    LLM-->>Agent: Generated code
    Agent->>Agent: Validate & iterate
    Agent-->>API: Final result
    API-->>UI: Response
```

### Generation and Validation Flow

```mermaid
sequenceDiagram
    participant Frontend
    participant API
    participant Agent as DiagramAgent
    participant LLM as Ollama
    participant Validator

    Frontend->>API: POST /diagrams/generate
    API->>Agent: generate_diagram()
    
    rect rgb(200, 220, 240)
        note right of Agent: Initialize State
        Agent->>Agent: determine_requirements()
        Agent->>Agent: setup_rag_if_enabled()
    end

    rect rgb(220, 240, 220)
        note right of Agent: Generation Phase
        Agent->>LLM: generate_with_llm()
        LLM-->>Agent: Raw diagram code
        Agent->>Agent: strip_comments()
    end

    rect rgb(240, 220, 220)
        note right of Agent: Validation Loop
        loop Until valid or max iterations
            Agent->>Validator: validate()
            Validator-->>Agent: Validation result
            
            alt has errors
                Agent->>LLM: fix_diagram()
                LLM-->>Agent: Fixed code
                Agent->>Agent: strip_comments()
            end
        end
    end

    Agent->>Agent: store_results()
    Agent-->>API: DiagramAgentOutput
    API-->>Frontend: JSON response
```

## Key Design Decisions

1. **Tool-Based Architecture**
   - Modular tool functions for specific tasks
   - Clear separation of concerns
   - Easier testing and maintenance
   - Configurable validation rules

2. **RAG Integration**
   - Code-aware diagram generation
   - Contextual understanding
   - Better accuracy for technical diagrams
   - Configurable similarity thresholds

3. **State Management**
   - Immutable state objects
   - Clear progression tracking
   - Comprehensive error handling
   - Detailed generation logs

4. **Storage Strategy**
   - SQLite for persistence
   - Version tracking
   - Metadata storage
   - Efficient querying

## Testing Strategy

1. **Unit Tests**
   - Individual tool testing
   - State management
   - RAG functionality
   - Validation rules

2. **Integration Tests**
   - End-to-end flows
   - API endpoints
   - Storage operations
   - RAG integration

3. **Test Data**
   - Sample code repositories
   - Various diagram types
   - Error cases
   - Performance scenarios

## Future Considerations

1. **Scalability**
   - Distributed RAG storage
   - Caching improvements
   - Batch processing
   - Multiple LLM support

2. **Features**
   - Real-time collaboration
   - Diagram templates
   - Custom validation rules
   - Export options

3. **Monitoring**
   - LLM performance tracking
   - RAG effectiveness metrics
   - User interaction analytics
   - Error rate monitoring
