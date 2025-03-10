# Style Guide for LLM Diagram Generator

## Code Style

### Python (Backend)
- Follow PEP (Python Enhancement Proposal) 8 style guidelines
- Use type hints for function parameters and return values
- Use docstrings for all functions, classes, and modules
- Maximum line length: 120 characters
- Use snake_case for variables and functions
- Use PascalCase for class names

### JavaScript/TypeScript (Frontend)
- Follow ESLint and Prettier configurations
- Use camelCase for variables and functions
- Use PascalCase for component names and classes
- Use descriptive names for functions and variables
- Prefer functional components with hooks for React

## Project Structure

### Backend
```
backend/
├── agents/           # LLM agent implementations
├── api/              # API endpoints
├── core/             # Core business logic
├── models/           # Data models
├── services/         # External service integrations (Ollama)
├── utils/            # Utility functions
└── tests/            # Test suite
```

### Frontend
```
frontend/
├── components/       # Reusable UI components
│   ├── chat/         # Chat panel components
│   ├── diagram/      # Diagram display components
│   └── shared/       # Shared UI components
├── hooks/            # Custom React hooks
├── pages/            # Page components
├── services/         # API service integration
├── store/            # State management
├── styles/           # CSS/SCSS files
└── utils/            # Utility functions
```

## UI/UX Design

### Design System
- Base UI on Material Design principles and components
- Implement dark theme as the default
- Provide light/dark theme toggle in application header
- Follow Material Design elevation system for component hierarchy

### Layout
- Use a responsive design with mobile-first approach
- Primary layout: Side-by-side chat and diagram panels on desktop, stacked on mobile
- Use consistent spacing throughout the application (8px increment system)
- Code editor panel should be collapsible/expandable
- Support split-view mode between diagram and code editor

### Color Palette
- Use Material Design color system
- Primary: #3B82F6 (blue-500)
- Secondary: #10B981 (green-500)
- Accent: #8B5CF6 (purple-500)
- Dark theme:
  - Background: #121212
  - Surface: #1E1E1E
  - Text: #FFFFFF (high emphasis), #B3B3B3 (medium emphasis)
- Light theme:
  - Background: #FFFFFF
  - Surface: #F5F5F5
  - Text: #121212 (high emphasis), #666666 (medium emphasis)

### Typography
- Primary font: Inter or system-ui
- Heading sizes:
  - H1: 24px (1.5rem)
  - H2: 20px (1.25rem)
  - H3: 16px (1rem)
- Body text: 14px (0.875rem)
- Use consistent font weights: 400 (regular), 500 (medium), 700 (bold)

### Components
- Use consistent rounding (border-radius: 6px)
- Buttons should have clear hover and active states
- Form elements should have clear focus states
- Use subtle animations for transitions (150-250ms)
- Code editor should use monospace font with syntax highlighting
- "Apply Changes" button should be prominently displayed with visual feedback on success/error
- Selected nodes in diagram should have a distinct highlight style
- Corresponding code sections should use background highlighting when nodes are selected
- Diagram type selector buttons should use consistent width with icon + text
- Selected diagram type button should have distinct active state styling
- Diagram type buttons should be arranged in a scrollable horizontal row on mobile

## Documentation

### Code Documentation
- Include JSDoc or equivalent for all public functions and components
- Document complex algorithms with explanatory comments
- Keep documentation updated when code changes

### User Documentation
- Include tooltips for complex features
- Provide examples for different diagram types
- Document keyboard shortcuts
- Include a "Getting Started" guide

## Diagram Styling
- Use consistent node sizes and spacing
- Maintain a consistent color theme for diagram elements
- Ensure sufficient contrast for text in diagrams
- Limit diagram complexity for better readability
- Support both Mermaid and PlantUML syntaxes
- Adapt styling to match current theme (light/dark)
- Selected nodes should have a distinct visual indicator (e.g., outline, glow effect)
- Nodes with syntax errors should have error indicators

## Git Workflow
- Use feature branches for development
- Write descriptive commit messages
- Reference issue numbers in commit messages
- Squash commits before merging to main branch

## Accessibility
- All interactive elements must be keyboard accessible
- Use ARIA (Accessible Rich Internet Applications) attributes appropriately
- Maintain a minimum contrast ratio of 4.5:1 for text
- Support screen readers for all important content
- Enable zoom and scaling without breaking layouts

## Interactive Behaviors
- Clicking a node in diagram highlights corresponding code section
- Cursor placement in code can highlight corresponding diagram elements when possible
- "Apply Changes" button should validate code before updating diagram
- Error messages should appear inline with code when syntax errors are detected
- Successful code application should provide subtle visual feedback
- Auto-sync option should be toggleable (for real-time updates vs. manual updates)
- Selecting a diagram type should visually indicate the active selection
- When "Auto" is selected, the system should infer the diagram type from the prompt
- Switching diagram types should provide a warning if there is already content in the prompt field
- Changing diagram type after generation should show a loading indicator during conversion
- After diagram type conversion, highlight changes with a subtle animation
- Conversion failures should show appropriate error messages with recovery options
