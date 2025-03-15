# ADR 006: Build Process and Deployment Requirements

## Status
Accepted

## Context
We need to formalize our build process and clarify deployment requirements, particularly addressing:

1. Windows-specific dependencies due to PlantUML.jar
2. Java runtime requirements for PlantUML
3. Build process standardization
4. Release packaging strategy
5. Installation requirements documentation

## Decision

### 1. Platform Requirements

We will explicitly support Windows as our primary platform due to:

- PlantUML.jar being a Windows-specific LGPL binary
- Consistent environment for development and deployment
- Simplified installation process

#### Consequences
- **Positive**: Clear platform target, simplified testing
- **Negative**: Limited platform support
- **Mitigation**: Future work could include cross-platform PlantUML support

### 2. Java Dependency Management

We will require Java 11+ for PlantUML operation:

- Clear documentation of Java requirements
- Verification steps in installation process
- Java path configuration guidance

#### Consequences
- **Positive**: Reliable PlantUML operation
- **Negative**: Additional installation requirement
- **Mitigation**: Clear installation instructions and validation steps

### 3. Build Process Standardization

Implement standardized build process:

1. **Backend**:
   - Python wheel package creation
   - Coverage and linting checks
   - Type checking with mypy

2. **Frontend**:
   - Production build with npm
   - Bundle size analysis
   - Test coverage requirements

#### Consequences
- **Positive**: Consistent build quality
- **Negative**: More complex build process
- **Mitigation**: Automated scripts and clear documentation

### 4. Release Packaging Strategy

Create comprehensive release packages:

1. **Package Contents**:
   ```
   diagram_generator_vX.Y.Z/
   ├── backend/
   │   ├── dist/
   │   └── requirements.txt
   ├── static/
   │   └── frontend build files
   ├── docs/
   ├── plantuml.jar
   ├── run.py
   └── README.md
   ```

2. **Distribution**:
   - Single ZIP archive
   - Windows-specific installers (future)
   - Version tracking across components

#### Consequences
- **Positive**: Simple distribution and installation
- **Negative**: Larger package size
- **Mitigation**: Consider optional component downloads

### 5. Installation Process

Standardize installation steps:

1. Prerequisites check
2. Virtual environment creation
3. Dependencies installation
4. Configuration validation
5. Service verification

#### Consequences
- **Positive**: Reliable installation process
- **Negative**: Multiple setup steps
- **Mitigation**: Provide setup scripts

## Technical Implementation

### 1. Build Automation

1. **Backend Checks**:
   ```bash
   pytest --cov=diagram_generator
   flake8 diagram_generator
   black --check diagram_generator
   mypy diagram_generator
   ```

2. **Frontend Checks**:
   ```bash
   npm run lint
   npm test
   npm run build
   npm run analyze
   ```

### 2. Release Creation

PowerShell script for release packaging:
```powershell
# Create release directory
mkdir release

# Copy backend files
Copy-Item "dist/*" "release/"
Copy-Item "requirements.txt" "release/"

# Copy frontend build
Copy-Item "frontend/dist/*" "release/static/" -Recurse

# Copy PlantUML
Copy-Item "frontend/public/plantuml.jar" "release/"

# Copy documentation
Copy-Item "docs/*" "release/docs/" -Recurse

# Create ZIP archive
Compress-Archive -Path "release/*" -DestinationPath "diagram_generator_vX.Y.Z.zip"
```

### 3. Validation Steps

Pre-release checklist:
- [ ] Backend tests pass
- [ ] Frontend tests pass
- [ ] Documentation updated
- [ ] Version numbers consistent
- [ ] PlantUML.jar included
- [ ] Clean installation test
- [ ] Ollama connectivity test
- [ ] Diagram generation test

## Security Considerations

1. **Binary Distribution**:
   - Verify PlantUML.jar checksums
   - Sign release packages
   - Document license compliance

2. **Runtime Security**:
   - Java security settings
   - Local network access controls
   - File system permissions

## Future Considerations

1. **Cross-Platform Support**:
   - Investigate platform-agnostic PlantUML alternatives
   - Create platform-specific installation packages
   - Docker containerization options

2. **Installation Improvements**:
   - One-click installer for Windows
   - Automated Java installation
   - Configuration wizard

3. **Distribution Enhancements**:
   - Component-based installation
   - Auto-update capability
   - Plugin system for extensions

## References

1. ADR-001: Project Outline
2. ADR-003: Architecture Simplification
3. ADR-004: UI Improvements
4. Build and Release Guide
5. System Requirements Documentation
