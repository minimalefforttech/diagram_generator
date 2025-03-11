# Diagram Generator Frontend

A modern web interface for the LLM Diagram Generator, built with React, TypeScript, and Material UI.

## Features

- Generate diagrams from natural language descriptions
- Support for multiple diagram types (Mermaid, PlantUML, C4)
- Live diagram preview
- Code editor with syntax highlighting
- Diagram validation
- Conversation interface for refining diagrams
- Responsive Material UI design

## Architecture

The frontend is built with a component-based architecture:

- **DiagramWorkspace**: Main container component
- **DiagramControls**: Input and diagram type controls
- **DiagramEditor**: Monaco-based code editor
- **DiagramPreview**: Live diagram preview with Mermaid support
- **ConversationPanel**: Chat interface for diagram refinement

## Backend Integration

The frontend integrates with the backend API through the `diagramService` in `src/services/api.ts`. The service provides methods for:

- Generating diagrams from descriptions
- Validating diagram syntax
- Converting between diagram formats
- Managing conversations

The integration includes fallback mechanisms to handle API errors gracefully, providing mock data when the backend is unavailable.

## Development

### Prerequisites

- Node.js 18.x or newer
- npm 9.x or newer

### Setup

1. Install dependencies:
   ```bash
   npm install
   ```

2. Start the development server:
   ```bash
   npm run dev
   ```

3. Access the application at http://localhost:5173

### Backend Connection

The frontend expects the backend to be running at http://localhost:8000. This can be configured in `vite.config.ts` and `src/services/api.ts`.

## Building for Production

```bash
npm run build
```

The build artifacts will be stored in the `dist/` directory.

## Testing

```bash
npm test
```

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── DiagramWorkspace/
│   │   │   ├── index.tsx
│   │   │   ├── DiagramControls.tsx
│   │   │   ├── DiagramEditor.tsx
│   │   │   └── DiagramPreview.tsx
│   │   └── ConversationPanel/
│   │       └── index.tsx
│   ├── services/
│   │   └── api.ts
│   ├── App.tsx
│   └── main.tsx
├── public/
└── index.html
```

## Future Enhancements

- User authentication
- Diagram history and versioning
- Export to various formats
- Custom diagram templates
- Collaborative editing
