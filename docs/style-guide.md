# Style Guide for LLM Diagram Generator

## Code Style

### Python (Backend)
- Follow PEP 8 style guidelines
- Use type hints for function parameters and return values
- Use docstrings for all functions, classes, and modules
- Maximum line length: 120 characters
- Use snake_case for variables and functions
- Use PascalCase for class names

### TypeScript (Frontend)
- Follow ESLint and Prettier configurations
- Use camelCase for variables and functions
- Use PascalCase for component names
- Use TypeScript interfaces for props and models
- Prefer functional components with hooks

## Project Structure

### Backend
```
python/
└── diagram_generator/
    ├── backend/
    │   ├── agents/          # Diagram generation agents
    │   ├── api/             # FastAPI endpoints
    │   ├── core/            # Core business logic
    │   ├── models/          # Data models and configs
    │   ├── services/        # External services (Ollama)
    │   ├── storage/         # Database and persistence
    │   └── utils/           # Utilities and helpers
    ├── services/           # Additional services
    └── tests/             # Test suites
```

### Frontend
```
frontend/
├── src/
│   ├── components/        # React components
│   │   ├── ConfigurationScreen.tsx  # Settings panel
│   │   ├── DiagramEditor.tsx       # Code editor
│   │   ├── DiagramHistory.tsx      # History browser
│   │   ├── DiagramPanel.tsx        # Diagram display
│   │   ├── OutputLog.tsx           # Generation logs
│   │   ├── StatusBar.tsx           # Status updates
│   │   └── ... 
│   ├── contexts/          # React contexts
│   │   ├── AppStateContext.tsx     # App state
│   │   ├── ThemeContext.tsx        # Theme
│   │   └── UIPreferencesContext.tsx # Preferences
│   ├── services/          # API client
│   ├── theme/            # Theme configuration
│   ├── types/            # TypeScript types
│   └── utils/            # Utilities
└── public/              # Static assets
```

## UI/UX Design

### Design System
- Material UI components and styling
- Responsive design with mobile support
- Dark theme by default with light option
- Consistent spacing (8px grid system)

### Layout
- Configuration panel at top
- Diagram workspace in center
- History browser in sidebar
- Status bar at bottom
- Editor panel as overlay/split view

### Color Palette
- Primary: #3B82F6 (blue-500)
- Secondary: #10B981 (green-500)
- Error: #DC2626 (red-600)
- Success: #059669 (green-600)
- Dark theme:
  - Background: #121212
  - Surface: #1E1E1E
  - Code: #1F2937
  - Text: #FFFFFF (high), #B3B3B3 (medium)
- Light theme:
  - Background: #FFFFFF
  - Surface: #F5F5F5
  - Code: #F9FAFB
  - Text: #111827 (high), #4B5563 (medium)

### Typography
- System font stack:
  ```css
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, 
               "Helvetica Neue", Arial, sans-serif;
  ```
- Code font:
  ```css
  font-family: "Fira Code", "JetBrains Mono", Menlo, Monaco, 
               Consolas, "Liberation Mono", monospace;
  ```
- Size scale:
  - H1: 24px
  - H2: 20px
  - H3: 16px
  - Body: 14px
  - Small: 12px

### Component Styling

#### Status Indicators
- Loading spinner for active processes
- Progress indicators for RAG processing
- Validation status icons
- Error/success notifications
- Current activity text in status bar

#### Configuration Panel
- Model selector with version info
- Syntax type buttons with icons
- Subtype dropdown when applicable
- RAG toggle with directory picker
- Description/prompt fields

#### Diagram Display
- Zoom controls
- Fit-to-view button
- Download/copy buttons
- Error highlights
- Selected node highlighting

#### Code Editor
- Syntax highlighting by type
- Line numbers
- Error underlining
- Matching bracket highlights
- Auto-indent
- Selection highlighting

#### History Browser
- Compact list view of diagrams
- Preview on hover
- Metadata display (type, date, etc)
- Delete confirmation
- Update/edit buttons

## Database Conventions

### Table Naming
- Use plural nouns: `diagrams`, `conversations`
- Use snake_case for table names
- Include descriptive prefixes if needed

### Column Naming
- Use snake_case
- Include foreign key prefix
- Use descriptive names

### Metadata
- Store as JSON when flexible schema needed
- Use specific columns for frequent queries
- Include timestamps for all records

## Git Commit Conventions

- Use semantic commit messages:
  ```
  feat: Add RAG support
  fix: Correct validation error handling
  docs: Update API documentation
  style: Format component styling
  refactor: Simplify diagram agent
  test: Add RAG integration tests
  ```

## Documentation Style

### Code Comments
- Use JSDoc for TypeScript
- Follow Google Python Style for docstrings
- Include examples for complex logic
- Document state management

### API Documentation
- Clear endpoint descriptions
- Complete request/response examples
- Error scenarios documented
- Authentication requirements

### User Documentation
- Task-based organization
- Clear step-by-step guides
- Screenshots for UI features
- Troubleshooting section

## Accessibility

- WCAG 2.1 AA compliance
- Keyboard navigation support
- Screen reader compatibility
- Color contrast requirements
- Focus management
- Error announcements
- Loading state indicators

## Error Handling

- User-friendly error messages
- Clear recovery actions
- Consistent error display
- Logging for debugging
- Graceful degradation
- Retry mechanisms
