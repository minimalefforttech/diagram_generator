# 005: Agent Improvements - Tool-Based Validation and Iteration

## Status

Proposed

## Context

The current `DiagramAgent` relies on the LLM to both generate and fix diagrams. This can be unreliable, leading to invalid diagrams or excessive iterations. We also want to improve the user experience by providing better feedback during the generation process and enabling code-aware diagram generation through RAG.

## Decision

We will refactor the `DiagramAgent` to incorporate the following improvements:

1. **Explicit Diagram Type**
   - The user will explicitly specify the diagram type (`mermaid` or `plantuml`) as an input
   - The agent will no longer attempt to infer this from the prompt
   - This ensures clarity and prevents potential misinterpretation

2. **Tool-Based Architecture**
   - The agent will use a series of internal "tools" (functions) to perform specific tasks:
     - `determine_requirements`: Analyzes prompt and diagram type to identify core requirements
     - `generate_diagram_code`: Calls the LLM to generate initial diagram code
     - `strip_comments`: Removes extraneous text (comments, backticks, language specifiers)
     - `validate_mermaid`: Validates Mermaid diagram syntax
     - `validate_plantuml`: Validates PlantUML diagram syntax and correct start tags

3. **Iterative Refinement**
   - Generate diagram code
   - Strip comments and other non-diagram text
   - Validate syntax using the appropriate validator
   - If validation fails, regenerate with error message as feedback
   - Repeat until valid or max iterations reached

4. **User Feedback**
   - Display agent's current activity in the frontend loading indicator
   - Notify user if max iterations reached without valid diagram
   - Display invalid diagrams in code editor view for troubleshooting

5. **RAG Integration**
   - Users can provide a directory of code/documentation as context
   - `determine_requirements` will:
     - Load documents via `RAGProvider`
     - Get relevant context based on the diagram description
     - Include context in subsequent LLM prompts
   - RAG context persists for subsequent requests in the same conversation

## Consequences

### Positive

- More reliable diagram generation through systematic validation
- Better user experience with clear feedback
- Code-aware diagram generation through RAG
- More maintainable and testable code through tool-based architecture
- Clear separation of concerns between generation, validation, and refinement

### Negative

- Slight increase in code complexity due to tool-based architecture
- Additional processing time for RAG document loading and querying
- May require more iterations in some cases due to stricter validation

### Neutral

- More structured approach to diagram generation
- Changes confined to the agent layer, minimal impact on other components

## Implementation Notes

1. The tool-based architecture will be implemented as class methods within `DiagramAgent`
2. Each tool will have clear input/output contracts
3. RAG functionality will leverage existing `RAGProvider` implementation
4. Validation tools will use the existing `DiagramValidator` class
5. The frontend loading indicator will be updated based on the agent's state
