# Class Structure

```mermaid
classDiagram
    %% Backend Service Classes
    class OllamaService {
        -api_url: string
        -model: string
        +generate(prompt: string, temperature: float): Response
        +is_available(): boolean
        +get_model_info(): Dict
    }

    class Storage {
        -db_path: string
        +save_diagram(diagram: DiagramRecord)
        +get_diagram(id: string): DiagramRecord
        +get_all_diagrams(): List[DiagramRecord]
        +delete_diagram(id: string)
        +save_conversation(conv: ConversationRecord)
        +clear_diagrams()
    }

    %% Agent Classes
    class DiagramAgent {
        -ollama: OllamaAPI
        -storage: Storage
        -default_model: string
        +generate_diagram(description: str, diagram_type: str, options: DiagramGenerationOptions): DiagramAgentOutput
        +update_diagram(code: str, update_notes: str, diagram_type: str): DiagramAgentOutput
        +run_agent(input: DiagramAgentInput): DiagramAgentOutput
        -determine_requirements(description: str, diagram_type: DiagramType, rag_directory: str): Dict
        -generate_with_llm(description: str, diagram_type: str, context: str, config: AgentConfig): Dict
        -validate_mermaid(code: str): ValidationResult
        -validate_plantuml(code: str): ValidationResult
        -fix_diagram(code: str, diagram_type: str, errors: List[str]): str
        -strip_comments(code: str): str
        -detect_diagram_type(description: str): str
        -get_syntax_rules(syntax_type: str): str
        -enhance_query_for_diagram(description: str, diagram_type: DiagramType): str
        -store_results(state: DiagramAgentState)
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
        +conversation_id: str
        +diagram_id: str
        +completed: bool
        +requirements: Dict
        +rag_provider: RAGProvider
        +current_activity: str
    }

    class DiagramAgentInput {
        +description: str
        +diagram_type: str
        +options: DiagramGenerationOptions
        +rag_context: Optional[str]
    }

    class DiagramAgentOutput {
        +code: str
        +diagram_type: str
        +notes: List[str]
        +valid: bool
        +iterations: int
        +diagram_id: str
        +conversation_id: str
    }

    class RAGProvider {
        -config: RAGConfig
        -ollama_base_url: str
        -docs: List[Document]
        -embeddings: Dict
        +load_docs_from_directory(dir: str): bool
        +get_relevant_context(query: str): SearchResult
        +stats: RAGProviderStats
    }

    class DiagramValidator {
        +validate(code: str, type: DiagramType): ValidationResult
        +validate_mermaid(code: str): ValidationResult
        +validate_plantuml(code: str): ValidationResult
    }

    %% Model Classes
    class DiagramGenerationOptions {
        +rag: RAGConfig
        +agent: AgentConfig
    }

    class RAGConfig {
        +enabled: bool
        +api_doc_dir: str
        +similarity_threshold: float
    }

    class AgentConfig {
        +enabled: bool
        +model_name: str
        +temperature: float
        +max_iterations: int
        +system_prompt: str
    }

    class DiagramRecord {
        +id: str
        +description: str
        +diagram_type: str
        +code: str
        +created_at: datetime
        +metadata: Dict
    }

    class ConversationRecord {
        +id: str
        +diagram_id: str
        +messages: List[ConversationMessage]
        +created_at: datetime
        +updated_at: datetime
        +metadata: Dict
    }

    class ConversationMessage {
        +role: str
        +content: str
        +timestamp: datetime
        +metadata: Dict
    }

    class DiagramType {
        <<enumeration>>
        MERMAID
        PLANTUML
    }

    class DiagramSubType {
        <<enumeration>>
        AUTO
        FLOWCHART
        SEQUENCE
        CLASS
        STATE
        ER
        MINDMAP
        +from_string(s: str): DiagramSubType
        +for_syntax(type: DiagramType): List[DiagramSubType]
    }

    %% Relationships
    DiagramAgent --> OllamaService : uses
    DiagramAgent --> Storage : uses
    DiagramAgent --> RAGProvider : uses
    DiagramAgent --> DiagramValidator : uses
    DiagramAgent -- DiagramAgentState : manages
    DiagramAgent -- DiagramAgentInput : processes
    DiagramAgent -- DiagramAgentOutput : produces
    DiagramAgentState --> RAGProvider : contains
    DiagramGenerationOptions *-- RAGConfig : contains
    DiagramGenerationOptions *-- AgentConfig : contains
    Storage -- DiagramRecord : manages
    Storage -- ConversationRecord : manages
    ConversationRecord *-- ConversationMessage : contains
    RAGProvider --> OllamaService : uses for embeddings
    DiagramValidator -- ValidationResult : produces
