# User Journey

```mermaid
flowchart TD
    Start([User starts application])
    
    subgraph Config[Configuration]
        SelectModel[Select Ollama model]
        SelectSyntax[Select diagram syntax]
        SelectSubtype[Select diagram subtype]
        EnableRAG[Enable RAG]
        SelectContext[Select code context directory]
        EnterPrompt[Enter diagram prompt]
        AddDescription[Add optional description]
    end
    
    subgraph Generation[Generation Process]
        ValidateConfig[Validate settings]
        ShowStatus[Show status indicator]
        
        subgraph RAG[RAG Processing]
            ProcessFiles[Process code files]
            GenerateEmbeddings[Generate embeddings]
            FindContext[Find relevant context]
        end
        
        subgraph DiagramGen[Diagram Generation]
            CreateDiagram[Generate diagram]
            ValidateSyntax[Validate syntax]
            FixIssues[Fix issues]
            StoreResult[Store result]
        end
    end
    
    subgraph Workspace[Diagram Workspace]
        ViewDiagram[View generated diagram]
        ViewCode[View diagram code]
        EditCode[Edit code manually]
        ViewOutput[View generation output]
    end

    subgraph History[History Management]
        OpenHistory[Open history browser]
        ViewHistoryItem[View historical diagram]
        DeleteDiagram[Delete diagram]
        ViewMetadata[View metadata]
    end

    subgraph Updates[Diagram Updates]
        SelectDiagram[Select diagram to update]
        EnterChanges[Enter update description]
        GenerateUpdate[Generate update]
        ValidateUpdate[Validate changes]
        SaveUpdate[Save updated version]
    end

    %% Main Flow
    Start --> Config
    
    %% Configuration Flow
    SelectModel --> SelectSyntax
    SelectSyntax --> SelectSubtype
    SelectSubtype --> EnableRAG
    
    EnableRAG --> RAGChoice{RAG enabled?}
    RAGChoice -- Yes --> SelectContext
    RAGChoice -- No --> EnterPrompt
    SelectContext --> EnterPrompt
    
    EnterPrompt --> AddDescription
    AddDescription --> ValidateConfig
    
    %% Generation Flow
    ValidateConfig --> ConfigValid{Config valid?}
    ConfigValid -- No --> Config
    ConfigValid -- Yes --> ShowStatus
    
    ShowStatus --> RAGEnabled{RAG enabled?}
    RAGEnabled -- Yes --> ProcessFiles
    ProcessFiles --> GenerateEmbeddings
    GenerateEmbeddings --> FindContext
    FindContext --> CreateDiagram
    RAGEnabled -- No --> CreateDiagram
    
    %% Generation Loop
    CreateDiagram --> ValidateSyntax
    ValidateSyntax --> SyntaxValid{Valid?}
    SyntaxValid -- No --> FixIssues
    FixIssues --> ValidateSyntax
    SyntaxValid -- Yes --> StoreResult
    
    StoreResult --> ViewDiagram
    
    %% Workspace Interactions
    ViewDiagram --> WorkspaceOptions{Select action}
    WorkspaceOptions -- Edit --> ViewCode
    WorkspaceOptions -- Output --> ViewOutput
    WorkspaceOptions -- History --> OpenHistory
    WorkspaceOptions -- Update --> SelectDiagram
    
    ViewCode --> EditCode
    EditCode --> ValidateEdits{Valid edits?}
    ValidateEdits -- No --> ShowErrors[Show validation errors]
    ShowErrors --> EditCode
    ValidateEdits -- Yes --> ViewDiagram
    
    %% History Flow
    OpenHistory --> ViewHistoryItem
    ViewHistoryItem --> HistoryOptions{Select action}
    HistoryOptions -- Delete --> DeleteDiagram
    HistoryOptions -- Details --> ViewMetadata
    HistoryOptions -- Update --> SelectDiagram
    DeleteDiagram --> OpenHistory
    
    %% Update Flow
    SelectDiagram --> EnterChanges
    EnterChanges --> GenerateUpdate
    GenerateUpdate --> ValidateUpdate
    ValidateUpdate --> UpdateValid{Valid update?}
    UpdateValid -- No --> FixUpdate[Fix issues]
    FixUpdate --> ValidateUpdate
    UpdateValid -- Yes --> SaveUpdate
    SaveUpdate --> ViewDiagram

    style Config fill:#f5f5f5,stroke:#333,stroke-width:2px
    style Generation fill:#e8f4f8,stroke:#333,stroke-width:2px
    style RAG fill:#f0f0f8,stroke:#333,stroke-width:2px
    style DiagramGen fill:#f8f0f8,stroke:#333,stroke-width:2px
    style Workspace fill:#f0f8f0,stroke:#333,stroke-width:2px
    style History fill:#f8f8f0,stroke:#333,stroke-width:2px
    style Updates fill:#f8f0f0,stroke:#333,stroke-width:2px
```

## Key Features

1. **Configuration**
   - Model selection
   - Diagram syntax and subtype selection
   - RAG configuration
   - Prompt and description entry

2. **Status Updates**
   - Real-time status indicator
   - Generation progress
   - Error notifications
   - Success confirmation

3. **RAG Integration**
   - Directory selection
   - File processing
   - Context matching
   - Enhanced generation

4. **Workspace Features**
   - Diagram visualization
   - Code editing
   - Output logging
   - Manual validation

5. **History Management**
   - Browse historical diagrams
   - View metadata
   - Delete diagrams
   - Update existing diagrams

6. **Update Flow**
   - Select diagram to update
   - Describe changes
   - Validate updates
   - Save new version
