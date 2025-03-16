# Sequence Diagrams: Core Flows

This document contains sequence diagrams illustrating the main flows in the system.

## 1. Diagram Generation with RAG

```mermaid
sequenceDiagram
    participant Client
    participant API as FastAPI
    participant Agent as DiagramAgent
    participant RAG as RAGProvider
    participant OS as OllamaService
    participant DB as Storage
    
    Client->>API: POST /diagrams/generate (with RAG)
    API->>Agent: generate_diagram(description, options)
    
    rect rgb(200, 220, 240)
        note right of Agent: Requirements Phase
        Agent->>Agent: determine_requirements()
        
        opt RAG Enabled
            Agent->>RAG: load_docs_from_directory()
            RAG->>OS: generate_embeddings()
            OS-->>RAG: embeddings
            Agent->>Agent: enhance_query_for_diagram()
            Agent->>RAG: get_relevant_context()
            RAG-->>Agent: code context
            Agent->>Agent: format context section
        end
    end
    
    rect rgb(220, 240, 220)
        note right of Agent: Generation Phase
        Agent->>Agent: setup_prompt()
        Agent->>OS: generate_with_llm()
        OS-->>Agent: raw diagram code
        Agent->>Agent: strip_comments()
    end
    
    rect rgb(240, 220, 220)
        note right of Agent: Validation Phase
        loop Until valid or max iterations
            Agent->>Agent: validate()
            
            alt has errors
                Agent->>OS: fix_diagram()
                OS-->>Agent: fixed code
                Agent->>Agent: strip_comments()
            end
        end
    end
    
    Agent->>DB: store_results()
    Agent-->>API: DiagramAgentOutput
    API-->>Client: JSON response
```

## 2. Diagram Update Flow

```mermaid
sequenceDiagram
    participant Client
    participant API as FastAPI
    participant Agent as DiagramAgent
    participant DB as Storage
    participant OS as OllamaService
    
    Client->>API: POST /diagrams/{id}/update
    API->>DB: get_diagram(id)
    DB-->>API: DiagramRecord
    
    API->>Agent: update_diagram(code, update_notes)
    
    rect rgb(220, 240, 220)
        note right of Agent: Update Phase
        Agent->>Agent: create_update_prompt()
        Agent->>OS: generate_with_llm()
        OS-->>Agent: updated code
        Agent->>Agent: strip_comments()
    end
    
    rect rgb(240, 220, 220)
        note right of Agent: Validation Phase
        loop Until valid or max iterations
            Agent->>Agent: validate()
            
            alt has errors
                Agent->>OS: fix_diagram()
                OS-->>Agent: fixed code
                Agent->>Agent: strip_comments()
            end
        end
    end
    
    Agent->>DB: save_diagram()
    Agent-->>API: DiagramAgentOutput
    API-->>Client: JSON response
```

## 3. History Management Flow

```mermaid
sequenceDiagram
    participant Client
    participant API as FastAPI
    participant DB as Storage
    
    alt Get History
        Client->>API: GET /diagrams/history
        API->>DB: get_all_diagrams()
        DB-->>API: List[DiagramRecord]
        API-->>Client: DiagramHistoryItems
        
    else Get Single Diagram
        Client->>API: GET /diagrams/diagram/{id}
        API->>DB: get_diagram(id)
        DB-->>API: DiagramRecord
        API-->>Client: DiagramResponse
        
    else Delete Diagram
        Client->>API: DELETE /diagrams/diagram/{id}
        API->>DB: delete_diagram(id)
        DB-->>API: Success
        API-->>Client: Success response
        
    else Clear History
        Client->>API: DELETE /diagrams/clear
        API->>DB: clear_diagrams()
        DB-->>API: Success
        API-->>Client: Success with count
    end
```

## 4. Error Handling Flow

```mermaid
sequenceDiagram
    participant Client
    participant API as FastAPI
    participant Agent as DiagramAgent
    participant OS as OllamaService
    participant Logger

    Client->>API: Any request
    
    alt Invalid Request
        API->>Logger: log_error()
        API-->>Client: 400 Bad Request
        
    else RAG Directory Error
        API->>Agent: generate_diagram()
        Agent->>Logger: log_error()
        Agent-->>API: Directory Error
        API-->>Client: 400 Bad Request
        
    else LLM Error
        API->>Agent: generate_diagram()
        Agent->>OS: generate_with_llm()
        OS->>Logger: log_error()
        OS-->>Agent: LLM Error
        Agent-->>API: Generation Error
        API-->>Client: 500 Internal Error
        
    else Generation Failed
        API->>Agent: generate_diagram()
        Agent->>OS: generate_with_llm()
        OS-->>Agent: Invalid Response
        Agent->>Logger: log_error()
        
        alt Max Iterations Reached
            Agent-->>API: Invalid Result
            API-->>Client: 200 OK with warnings
        else Other Error
            Agent-->>API: Error Details
            API-->>Client: 500 Internal Error
        end
    end

    Note over Logger: All errors include:
    Note over Logger: - Error details
    Note over Logger: - Stack trace
    Note over Logger: - Input parameters 
    Note over Logger: - Current state
```

## Notes

1. The tool-based approach in DiagramAgent provides:
   - Clear separation of concerns
   - Systematic validation and iteration
   - Detailed logging and error tracking
   - Configurable behavior

2. RAG integration enables:
   - Code-aware diagram generation
   - Context-sensitive refinements
   - Improved accuracy
   - Enhanced prompts

3. State management ensures:
   - Reliable progression tracking
   - Comprehensive error handling
   - Detailed generation logs
   - Proper cleanup

4. Storage integration provides:
   - Persistent diagram history
   - Version tracking
   - Metadata management
   - Quick retrieval
