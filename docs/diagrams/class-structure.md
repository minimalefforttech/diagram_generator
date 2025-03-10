# Class Structure

```mermaid
classDiagram
    %% Backend Classes
    class OllamaService {
        -apiUrl: string
        +getAvailableModels(): Model[]
        +generateCompletion(prompt: string): string
    }

    class DiagramGenerator {
        -llmService: LLMService
        +generateDiagram(prompt: string, diagramType: string): string
        +validateDiagram(code: string, diagramType: string): ValidationResult
        +refineDiagram(feedback: string, currentCode: string, diagramType: string): string
        +convertDiagramType(currentCode: string, sourceType: string, targetType: string): string
    }

    class ConversationManager {
        -conversations: Conversation[]
        +createConversation(): Conversation
        +saveConversation(conversation: Conversation)
        +getConversationHistory(): Conversation[]
        +deleteConversation(id: string)
    }

    class DiagramRepository {
        +saveDiagram(diagram: Diagram)
        +getDiagrams(): Diagram[]
        +getDiagramById(id: string): Diagram
        +deleteDiagram(id: string)
    }

    %% Frontend Classes
    class ThemeProvider {
        -currentTheme: Theme
        +toggleTheme(): void
        +getCurrentTheme(): Theme
        +applyTheme(theme: Theme): void
    }

    class DiagramPanel {
        -code: string
        -diagramType: string
        -selectedNode: string
        +renderDiagram()
        +handleNodeClick(nodeId: string)
        +exportDiagram(format: string)
        +zoomControl()
    }

    class CodeEditorPanel {
        -code: string
        -diagramType: string
        -selectedRange: Range
        +updateCode(newCode: string)
        +highlightSection(section: Range)
        +validateSyntax(): boolean
        +applyChanges()
    }

    class ChatPanel {
        -messages: Message[]
        -activeConversationId: string
        +sendMessage(text: string)
        +displayMessage(message: Message)
        +loadConversation(id: string)
    }

    class ModelSelector {
        -availableModels: Model[]
        -selectedModel: Model
        +loadModels()
        +selectModel(model: Model)
        +getSelectedModel(): Model
    }

    class HistoryBrowser {
        -diagrams: Diagram[]
        -conversations: Conversation[]
        +loadHistory()
        +selectDiagram(id: string)
        +viewChatContext(diagramId: string)
        +deleteDiagram(id: string)
        +searchHistory(query: string)
    }

    class DiagramTypeSelector {
        -diagramTypes: DiagramType[]
        -selectedType: DiagramType
        +selectType(type: DiagramType)
        +getSelectedType(): DiagramType
        +isAuto(): boolean
        +getTypeForPrompt(): string
        +convertExistingDiagram(currentCode: string, newType: DiagramType): void
    }

    %% Data Models
    class Diagram {
        +id: string
        +title: string
        +code: string
        +diagramType: string
        +createdAt: DateTime
        +conversationId: string
    }

    class Conversation {
        +id: string
        +messages: Message[]
        +diagramId: string
        +createdAt: DateTime
    }

    class Message {
        +id: string
        +sender: string
        +content: string
        +timestamp: DateTime
    }

    class ValidationResult {
        +valid: boolean
        +errors: Error[]
        +suggestions: string[]
    }

    %% Relationships
    OllamaService <-- DiagramGenerator
    DiagramRepository -- Diagram
    ConversationManager -- Conversation
    Conversation *-- Message
    DiagramPanel <-- CodeEditorPanel : highlights
    ChatPanel -- Conversation
    HistoryBrowser -- Diagram
    HistoryBrowser -- Conversation
    DiagramPanel -- Diagram : renders
    DiagramTypeSelector --> ChatPanel : enhances prompt
    ThemeProvider --> DiagramPanel : applies theme
```
