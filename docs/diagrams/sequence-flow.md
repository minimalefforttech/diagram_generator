# Sequence Diagrams: Core Flows

This document contains sequence diagrams illustrating the main flows in the system.

## 1. RAG Integration Flow

```mermaid
sequenceDiagram
    participant Client
    participant API as FastAPI
    participant RA as RAG Agent
    participant OS as OllamaService
    participant FS as File System

    Client->>API: POST /diagrams/generate (with RAG config)
    Note over API: Validate RAG directory
    API->>RA: load_docs_from_directory(path)
    
    RA->>FS: Read directory contents
    FS-->>RA: File list
    
    loop For each file
        RA->>FS: Read file content
        FS-->>RA: File content
        RA->>OS: Generate embeddings
        OS-->>RA: File embeddings
        RA->>RA: Index content
    end
    
    RA->>OS: Get context embeddings
    OS-->>RA: Context vector
    RA->>RA: Find relevant documents
    RA-->>API: Return RAG context
    
    API->>API: Incorporate context into prompt
    API-->>Client: Generation response with RAG
```

## 2. Diagram Generation Flow

```mermaid
sequenceDiagram
    participant Client
    participant API as FastAPI
    participant DG as DiagramGenerator
    participant OS as OllamaService
    participant LLM as Ollama LLM

    Client->>API: POST /diagrams/generate
    Note over API: Validate request params
    API->>DG: generate_diagram(description)
    
    DG->>DG: Build prompt template
    DG->>OS: generate_completion(prompt)
    
    alt Cache Hit
        OS->>OS: Return cached response
    else Cache Miss
        OS->>LLM: Send prompt
        LLM-->>OS: Return response
        OS->>OS: Cache response
    end
    
    OS-->>DG: Return completion
    DG->>DG: Extract diagram code
    DG->>DG: Validate syntax
    DG-->>API: Return result
    API-->>Client: JSON response
```

## 3. Diagram Validation Flow

```mermaid
sequenceDiagram
    participant Client
    participant API as FastAPI
    participant DA as DiagramAgent
    participant VAL as DiagramValidator
    participant OS as OllamaService
    participant LLM as Ollama LLM

    Client->>API: POST /diagrams/validate
    API->>DA: validate_diagram(code, type)
    
    DA->>VAL: validate(code, type)
    VAL->>VAL: Check syntax structure
    
    alt Basic Validation Fails
        VAL-->>DA: Return errors
        DA-->>API: Return validation errors
        API-->>Client: Validation response
    else Basic Validation Passes
        VAL->>OS: Request semantic validation
        OS->>LLM: Process validation
        LLM-->>OS: Validation results
        OS-->>VAL: Return validation
        VAL-->>DA: Combined validation results
        DA-->>API: Return validation details
        API-->>Client: Complete validation response
    end

    alt Auto-Fix Requested
        Client->>API: POST /diagrams/fix
        API->>DA: fix_diagram(code, errors)
        DA->>OS: Request fixes
        OS->>LLM: Generate fixes
        LLM-->>OS: Fixed code
        OS-->>DA: Return fixes
        DA->>VAL: Validate fixes
        VAL-->>DA: Validation result
        DA-->>API: Return fixed code
        API-->>Client: Fixed diagram code
    end
```

## 4. Diagram Conversion Flow

```mermaid
sequenceDiagram
    participant Client
    participant API as FastAPI
    participant DG as DiagramGenerator
    participant OS as OllamaService
    participant LLM as Ollama LLM

    Client->>API: POST /diagrams/convert
    API->>DG: convert_diagram(diagram, source, target)
    
    DG->>DG: Build conversion prompt
    DG->>OS: generate_completion(prompt)
    
    OS->>LLM: Send conversion request
    LLM-->>OS: Return converted diagram
    
    OS-->>DG: Return response
    DG->>DG: Validate conversion
    DG-->>API: Return converted diagram
    API-->>Client: JSON response
```

## 5. Error Handling Flow

```mermaid
sequenceDiagram
    participant Client
    participant API as FastAPI
    participant DA as DiagramAgent
    participant OS as OllamaService
    participant LLM as Ollama LLM
    participant Logger

    Client->>API: POST /diagrams/*
    
    alt Invalid Request
        API->>Logger: Log validation error
        API-->>Client: 400 Bad Request + error details
    else Invalid RAG Directory
        API->>DA: method_call()
        DA->>Logger: Log RAG error
        DA-->>API: Directory Error
        API-->>Client: 400 Bad Request + directory error
    else LLM Unavailable
        API->>DA: method_call()
        DA->>OS: generate_completion()
        OS-xLLM: Connection Failed
        OS->>Logger: Log connection error
        OS-->>DA: Service Error
        DA-->>API: Error + Retry Strategy
        API-->>Client: 503 + Retry-After
    else Generation Error
        API->>DA: method_call()
        DA->>OS: generate_completion()
        OS->>LLM: Send Request
        LLM-->>OS: Invalid Response
        OS->>Logger: Log generation error
        OS-->>DA: Parse Error
        DA->>DA: Attempt recovery
        alt Recovery Successful
            DA-->>API: Recovered Result
            API-->>Client: 200 OK + Warning Header
        else Recovery Failed
            DA-->>API: Error Details
            API-->>Client: 500 + Detailed Error
        end
    end

    Note over Logger: All errors include:
    Note over Logger: - Error type and message
    Note over Logger: - Stack trace
    Note over Logger: - Input that caused error
    Note over Logger: - System state
```

## Notes

1. All flows use async/await for better performance
2. Error handling is implemented at each layer
3. Caching is used where appropriate to improve response times
4. Validation occurs after generation and conversion
5. Each component has specific responsibilities:
   - API: Request handling and response formatting
   - DiagramGenerator: Business logic and orchestration
   - OllamaService: LLM communication and caching
