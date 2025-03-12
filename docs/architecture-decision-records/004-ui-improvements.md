# ADR 004: UI Improvements and Theme System

## Status
Proposed

## Context
After initial implementation of the backend system and basic UI components, we need to enhance the user experience with better UI flow, theme options, navigation capabilities, and diagram export functionality. The current interface lacks:

1. A structured setup flow for diagram configuration
2. Sufficient theme customization options
3. Diagram navigation and export capabilities
4. Clear visual feedback for states (loading, error, success)
5. Intuitive UI controls for common operations
6. Visibility into agent iterations for diagnostic purposes
7. Proper persistence and management of logs and history

These issues impact user satisfaction and limit the tool's utility for different use cases and preferences.

## Decision

We will implement the following UI improvements:

### 1. Multi-Screen Workflow & Configuration

Create a structured multi-screen setup process for diagram creation:

- Implement discrete screens for different workflow stages:
  - Initial configuration screen (first screen)
  - Diagram workspace screen (second screen)
- Add dedicated configuration screen with:
  - Description input field
  - Syntax selection (Mermaid/PlantUML)
  - Service selection (Ollama)
  - Model selection dropdown (e.g., llama3:1.8b)
- Implement frontend validation to prevent proceeding until:
  - Selected service (e.g., Ollama) is verified as running
  - A valid model is selected from available options
  - Description field has sufficient content
- Add diagram workspace with agent iteration counter (for diagnostics)
- Include code editor toggle capability for direct syntax editing

### 2. Comprehensive Theme System

Implement a flexible theme system with multiple customization options:

- Add light/dark mode toggle with persistent preference storage
- Support three color palette options:
  - Greyscale: Neutral tones for professional environments
  - Bold: High contrast with primary colors (red, green, blue)
  - Pastel: Soft colors for reduced eye strain
- Pass theme selection to backend with diagram requests
- Allow theme changes via both UI controls and chat interface
- Provide theme selection via buttons with color previews

### 3. Diagram Navigation & Type Management

Add essential diagram interaction features:

- Implement diagram navigation controls (zoom, pan)
- Add PNG export capability for both Mermaid and PlantUML diagrams
- Support history selection for reviewing previous diagram iterations
- Enable syntax type switching post-creation (e.g., Mermaid to PlantUML)
- Provide dropdown for selecting specific diagram types:
  - Flow diagrams
  - Sequence diagrams
  - Timeline diagrams
  - Class diagrams
  - Other types as supported
- Default to "auto" type detection if not explicitly selected
- Implement backend service that provides available syntax and types

### 4. UI Polish & Feedback

Improve overall usability and feedback:

- Replace abstract icons with combined text+icon buttons for clarity
- Implement log management controls:
  - Clear logs button that purges both frontend display and backend storage
  - Log filtering options
- Add prominent "New Diagram" button with cancellation option 
  - New button returns to configuration screen
  - Cancel returns to current diagram workspace
- Display clear loading/validation states during operations
- Show agent iteration count for diagnostic purposes

### 5. Chat Experience Improvements

Optimize the chat interaction flow:

- Support model changes without requiring text input
  - Allow selecting a new model and submitting without text
  - Use default prompt "Generate" when only model is changed
- Use optimized context in API requests:
  - Send only the last chat message
  - Include current diagram syntax
  - Don't send full chat history
- Improve interaction with diagram history:
  - Allow loading previous iterations of diagrams
  - Restore associated chat context when loading history
  - Enable resuming work from any historical point

## Implementation Plan

### Phase 1: Multi-Screen Workflow
1. Create configuration screen component with validation logic
2. Implement service/model validation with backend connectivity check
3. Design workflow for transitioning between configuration and workspace screens
4. Add "New Diagram" button with confirmation/cancellation flow

### Phase 2: Theme System & UI Polish
1. Implement light/dark mode toggle with localStorage persistence
2. Add color palette selection framework (Greyscale, Bold, Pastel)
3. Replace icons with text+icon buttons
4. Improve loading and validation state displays

### Phase 3: Diagram Management
1. Implement agent iteration counter display
2. Add code editor toggle functionality
3. Create backend service for available syntax and diagram types
4. Implement diagram type dropdown with auto-detection fallback

### Phase 4: History & Log Management
1. Create history selection interface for previous iterations
2. Implement proper log clearing functionality (frontend and backend)
3. Add log filtering capabilities
4. Create state management for preserving context between screens

### Phase 5: Advanced Features
1. Add zoom and pan controls to diagram display
2. Implement PNG export functionality
3. Enable syntax switching capability (Mermaid/PlantUML)
4. Add support for specialized diagram types

## Consequences

### Positive
- Improved user experience with intuitive multi-stage workflow
- Better diagram configuration options with validation
- Greater accessibility through theme customization
- Enhanced utility with export and navigation features
- Better visibility into system operations with iteration counter
- More flexible diagram creation and modification workflow
- Proper log management and history navigation

### Negative
- Increased frontend complexity with multi-screen workflow
- Additional API endpoints needed for service validation and type information
- Additional testing requirements for different paths through the UI
- Potential performance impact from more UI features
- Need for additional documentation for new features

### Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| Theme inconsistencies across components | Create comprehensive theme tokens system |
| Service validation delays | Implement caching of service status with reasonable TTL |
| Performance issues with complex diagrams | Implement lazy rendering for large diagrams |
| Users confused by multi-screen flow | Add clear progress indicators and navigation cues |
| History/log storage growing too large | Implement retention policies and pagination |
| Export compatibility issues | Test exports across different browsers |
| Increased bundle size | Implement code-splitting and lazy loading |

## Success Metrics

We will measure the success of these UI improvements by:

1. User Experience
   - Task completion time for diagram creation
   - Number of iterations required for satisfactory diagrams
   - User-reported satisfaction with interface
   - Frequency of direct code editing vs. chat-based editing

2. Feature Adoption
   - Frequency of theme changes
   - Export feature usage
   - Navigation control usage
   - History selection usage
   - Diagram type selection patterns

3. System Performance
   - Time to load and render diagrams
   - Responsiveness during interactions
   - Memory usage with complex diagrams
   - Backend log storage efficiency

## References

- ADR-001: Project Outline - LLM Diagram Generator
- ADR-002: Initial Implementation Approach
- ADR-003: Architecture Simplification