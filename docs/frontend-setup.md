# Frontend Development Setup

## Prerequisites

### 1. Node.js Installation
1. Download Node.js LTS (18.x or newer) from [https://nodejs.org/](https://nodejs.org/)
2. Run the installer (node-x.x.x-x64.msi)
3. Follow installation wizard with default settings
4. Verify installation by opening a new terminal:
   ```bash
   node --version
   npm --version
   ```

### 2. Development Tools
- Visual Studio Code or preferred IDE
- Git for version control

## Project Setup

1. Install project dependencies:
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

- `npm run dev` - Start development server
- `npm run build` - Build production bundle
- `npm run preview` - Preview production build locally
- `npm run lint` - Run ESLint
- `npm test` - Run tests

## Project Structure

```
frontend/
├── src/               # Source files
│   ├── components/    # React components
│   ├── hooks/        # Custom React hooks
│   ├── services/     # API services
│   ├── types/        # TypeScript type definitions
│   ├── utils/        # Utility functions
│   └── App.tsx       # Root component
├── public/           # Static files
└── index.html        # HTML template
```

## Technology Stack

- React 18
- TypeScript
- TailwindCSS
- Vite (Build tool)
- React Query (API state management)
- React Router (Navigation)

## Code Style & Guidelines

1. Use TypeScript for all new files
2. Follow ESLint & Prettier configuration
3. Write tests for components and utilities
4. Follow React best practices and hooks guidelines

## Development Workflow

1. Create feature branch from main
2. Implement changes with tests
3. Run linting and tests
4. Create pull request
5. Address review feedback
6. Merge to main branch

## Troubleshooting

### Common Issues

1. **Node modules not found**
   ```bash
   rm -rf node_modules
   npm install
   ```

2. **Port conflicts**
   - Default port is 5173
   - Change in vite.config.ts if needed

3. **Type errors**
   - Ensure TypeScript version matches project
   - Check tsconfig.json settings
   - Run `tsc` to verify types
