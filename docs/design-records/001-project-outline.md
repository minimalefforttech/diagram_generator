# ADR 001: Project Outline - LLM Diagram Generator

## Status
Accepted

## Context
We need to create a tool that leverages LLMs (Large Language Models) to generate and refine diagrams based on user prompts. The system should provide an interactive chat interface, display diagrams using Mermaid and PlantUML syntax, and allow for iterative refinement of the diagrams through natural language conversation.

## Decision

### System Architecture

We will create a web application with:

1. **Python Backend** using FastAPI with:
   - LangChain/LangGraph for LLM orchestration
   - Integration with Ollama for local model inference
   - Diagram validation and generation system

2. **Web Frontend** using React with:
   - Chat interface for user-LLM interaction
   - Diagram renderers for Mermaid and PlantUML
   - History management for past diagrams and conversations
   - Light/dark theme toggle with dark as default

### Key Components

#### Backend Components

1. **LLM Integration Layer**
   - Wrapper around Ollama API
   - Model selection capabilities
   - Prompt management and templating

2. **Diagram Generation System**
   - Generate Mermaid and PlantUML diagrams from prompts
   - Validate diagram syntax
   - Convert between diagram types when requested

3. **Conversation Management**
   - Stores chat history
   - Maintains context for iterative refinement
   - Handles state management

4. **Persistence Layer**
   - Stores diagram history
   - Manages user sessions
   - Implements CRUD (Create, Read, Update, Delete) operations for diagrams and conversations

#### Frontend Components

1. **Chat Panel**
   - Message display area
   - Input field for user prompts
   - Message history with timestamps

2. **Theme Toggle**
   - Switch between light and dark themes
   - Default to dark theme

3. **Diagram Type Selector**
   - Row of buttons for common diagram types (flowchart, sequence, class, etc.)
   - "Auto" option as default for type inference from prompt
   - Visual indication of the selected type
   - Appends selected type to prompt when submitted
   - Allows changing diagram type after generation with one click

4. **Diagram Panel**
   - Mermaid.js and PlantUML renderers
   - Zoom and pan controls
   - Export options (PNG - Portable Network Graphics, SVG - Scalable Vector Graphics)
   - Interactive node selection with code highlighting

5. **Code Editor Panel**
   - Syntax-highlighted editor for Mermaid/PlantUML code
   - Apply changes button to update diagram
   - Bidirectional selection sync with diagram panel
   - Error highlighting for syntax issues

6. **Model Selector**
   - Dropdown of available Ollama models
   - Model information display
   - Connection status indicator

7. **History Browser**
   - List of saved diagrams with previews
   - Associated chat context for each diagram
   - Search and filter capabilities
   - Delete functionality with confirmation

### Data Flow

1. User selects an Ollama model
2. User selects a specific diagram type or uses "Auto" default
3. User enters a prompt requesting a diagram
4. Backend processes the request through LangChain/LangGraph (with diagram type appended if specified)
5. Generation agent creates initial Mermaid diagram
6. Validation agent checks for syntax errors
7. Diagram is rendered in frontend using Mermaid.js
8. User can provide feedback to refine the diagram OR manually edit the Mermaid code
9. Manual edits are validated and applied to the diagram view when the user clicks "Apply Changes"
10. Selecting diagram elements highlights corresponding code sections and vice versa
11. Conversation, diagram, and code are saved to history
12. User can change diagram type after generation, triggering conversion of existing diagram

### Extension Points

1. **OpenRouter Integration** (future)
   - Abstract LLM provider interface to support multiple backends
   - Configuration for API keys and endpoints

2. **Additional Diagram Types**
   - Support for C4 diagrams in phase 2
   - Type-specific validation and rendering

## Consequences

### Positive

- Interactive diagram creation through natural language
- Self-validating system reduces errors in diagram syntax
- History feature enables reference to previous work
- Local LLM usage through Ollama provides privacy and control

### Negative

- Complexity in agent coordination
- Limited by capabilities of selected Ollama models
- Potential performance issues with large diagrams
- Need to keep Mermaid syntax knowledge updated in the system

### Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| LLM generates invalid Mermaid syntax | Implement robust validation agent with syntax correction |
| Complex diagrams may overwhelm the UI | Implement view controls and pagination/lazy loading |
| Context length limitations of LLMs | Implement efficient context summarization |
| User data privacy concerns | Store all data locally with clear deletion options |

## Implementation Plan

### Phase 1: Core Functionality
- Backend API with Ollama integration
- Basic chat interface
- Mermaid and PlantUML diagram rendering
- Single LLM for diagram generation
- Basic code editor with manual editing
- Light/dark theme support

### Phase 2: Enhanced Features
- History storage and retrieval with chat context
- Improved UI/UX for both panels
- Bidirectional selection between code and diagram
- Syntax validation for manual edits
- C4 diagram support

### Phase 3: Extensions
- OpenRouter integration
- Additional diagram types
- Export functionality improvements

## Technology Evaluation

### LLM Framework Alternatives

We evaluated several frameworks for LLM (Large Language Model) orchestration:

1. **LangChain/LangGraph** (Selected)
   - Strengths: Built-in agent system, workflow management via LangGraph, excellent support for multi-agent orchestration
   - Weaknesses: Can be complex, some overhead for simpler use cases
   - Fit: Well-suited for our multi-agent validation workflow and diagram generation pipeline

2. **CrewAI**
   - Strengths: Role-based agent collaboration, simpler API than LangChain in some cases
   - Weaknesses: Less mature ecosystem, fewer integrations
   - Fit: Could work well for agent roles but has less workflow management capabilities than LangGraph

3. **LlamaIndex**
   - Strengths: Excellent for RAG (Retrieval-Augmented Generation), data indexing
   - Weaknesses: Less focused on agent systems
   - Fit: Could complement our system if we add knowledge retrieval features later

4. **Semantic Kernel**
   - Strengths: Plugin architecture, good integration with Microsoft ecosystem
   - Weaknesses: More .NET oriented, though Python SDK (Software Development Kit) exists
   - Fit: Less aligned with our Python-based backend

5. **Custom Implementation with Direct API Calls**
   - Strengths: Maximum flexibility, no dependencies
   - Weaknesses: Would require building agent system from scratch
   - Fit: Would increase development time significantly

**Decision Rationale:** LangChain/LangGraph provides the most comprehensive solution for our multi-agent workflow requirements, Ollama integration, and extensibility needs. The agent system and graph-based workflow are particularly valuable for the diagram validation and refinement process.

## Technologies

- **Backend**: Python, FastAPI, LangChain, LangGraph, Ollama API (Application Programming Interface)
- **Frontend**: React, TypeScript, Mermaid.js, PlantUML renderer, Material Design components
- **Storage**: SQLite (initial), with option to migrate to PostgreSQL
- **Deployment**: Docker for containerization

## Evaluation Criteria

The success of this project will be measured by:
1. Accuracy of generated diagrams
2. User satisfaction with the interaction flow
3. Performance and responsiveness
4. Extensibility for future requirements
