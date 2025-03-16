# Frontend Development Setup

## Prerequisites

### 1. Node.js Installation
1. Download Node.js 18.x or newer from [https://nodejs.org/](https://nodejs.org/)
2. Run the installer for your platform
3. Verify installation:
   ```bash
   node --version  # Should be 18.x or higher
   npm --version
   ```

### 2. Development Tools
- Visual Studio Code (recommended)
- Git for version control
- Chrome/Firefox Developer Tools

## Project Setup

1. Install dependencies:
   ```bash
   # Navigate to frontend directory
   cd frontend
   
   # Install dependencies
   npm install
   ```

2. Start development server:
   ```bash
   npm run dev
   ```
   This will start the development server at http://localhost:5173

## Available Scripts

- `npm run dev` - Start development server with hot reload
- `npm run build` - Build production bundle
- `npm run preview` - Preview production build locally
- `npm run lint` - Run ESLint
- `npm run format` - Format code with Prettier

## Project Structure

```
frontend/
├── src/
│   ├── components/           # React components
│   │   ├── ChatPanel.tsx      # Diagram update interactions
│   │   ├── ConfigurationScreen.tsx  # Settings & generation
│   │   ├── DiagramEditor.tsx  # Code editor component
│   │   ├── DiagramHistory.tsx # History management
│   │   ├── DiagramPanel.tsx   # Diagram display
│   │   ├── ErrorBoundary.tsx  # Error handling
│   │   ├── Layout.tsx         # App layout structure
│   │   ├── ModelSelector.tsx  # LLM model selection
│   │   ├── OutputLog.tsx      # Generation output display
│   │   ├── PaletteSelector.tsx # Theme customization
│   │   ├── SideBar.tsx        # Navigation sidebar
│   │   ├── StatusBar.tsx      # Status updates
│   │   └── ThemeToggle.tsx    # Dark/light mode
│   │
│   ├── contexts/            # React contexts
│   │   ├── AppStateContext.tsx  # Application state
│   │   ├── ThemeContext.tsx     # Theme management
│   │   └── UIPreferencesContext.tsx # User preferences
│   │
│   ├── services/           # API services
│   │   └── api.ts           # Backend API client
│   │
│   ├── theme/             # Theme configuration
│   │   └── themeGenerator.ts # Dynamic theme generation
│   │
│   ├── types/             # TypeScript types
│   │   ├── configs.ts       # Configuration types
│   │   └── generation.ts    # Generation types
│   │
│   ├── utils/             # Utility functions
│   │   └── editorConfig.ts  # Editor configuration
│   │
│   ├── App.tsx           # Root component
│   ├── main.tsx         # Entry point
│   └── index.css        # Global styles
│
└── public/              # Static assets
    └── plantuml.jar    # PlantUML renderer
```

## Technology Stack

- **Core**:
  - React 18
  - TypeScript 5
  - Vite 4

- **UI Framework**:
  - Material UI (@mui/material)
  - @emotion/react
  - @emotion/styled

- **Diagram Rendering**:
  - mermaid.js - Mermaid diagram rendering
  - plantuml-encoder - PlantUML support

- **State Management**:
  - React Context API
  - Custom hooks for business logic

## Key Features

### 1. Configuration Panel
- Model selection
- Diagram type selection (Mermaid/PlantUML)
- Diagram subtype configuration
- RAG settings
- Generation options

### 2. Diagram Workspace
- Real-time diagram preview
- Code editor with syntax highlighting
- Error display and validation
- Status indicators

### 3. History Management
- Browse generated diagrams
- View historical versions
- Delete diagrams
- Update existing diagrams

### 4. Theme System
- Light/dark mode support
- Custom color palettes
- Dynamic theme generation
- Persistent preferences

## Development Guidelines

1. **Code Style**
   - Use TypeScript for all new components
   - Follow ESLint & Prettier configuration
   - Use functional components with hooks
   - Implement error boundaries

2. **Component Structure**
   - Clear separation of concerns
   - Custom hooks for logic
   - Props interface definitions
   - Error handling

3. **State Management**
   - Use contexts for shared state
   - Local state for component-specific data
   - Optimize re-renders

4. **Error Handling**
   - Implement error boundaries
   - Display user-friendly errors
   - Log errors appropriately

## Troubleshooting

### Common Issues

1. **Node Modules Issues**
   ```bash
   rm -rf node_modules
   rm package-lock.json
   npm install
   ```

2. **Build Errors**
   - Check TypeScript version
   - Verify module imports
   - Clear vite cache:
     ```bash
     npm run clean
     ```

3. **Theme Issues**
   - Check ThemeContext setup
   - Verify emotion dependencies
   - Clear localStorage if needed

4. **Diagram Rendering**
   - Verify mermaid/plantuml setup
   - Check browser console for errors
   - Validate diagram syntax
