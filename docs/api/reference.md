# API Reference

This document describes the publicly exposed API endpoints for diagram generation, management, and history tracking.

## Table of Contents

1. [Introduction](#introduction)
2. [Core Endpoints](#core-endpoints)
   - [POST /diagrams/generate](#post-diagramsgenerate)
   - [GET /diagrams/syntax-types](#get-diagramssyntax-types)
   - [POST /diagrams/diagram/{id}/update](#post-diagramsdiagramidupdate)
3. [History Management](#history-management)
   - [GET /diagrams/history](#get-diagramshistory)
   - [GET /diagrams/diagram/{id}](#get-diagramsdiagramid)
   - [GET /diagrams/diagram/{id}/iterations](#get-diagramsdiagramiditerations)
   - [DELETE /diagrams/diagram/{id}](#delete-diagramsdiagramid)
   - [DELETE /diagrams/clear](#delete-diagramsclear)
4. [Error Handling](#error-handling)

## Introduction

The system provides RESTful API endpoints for:
1. Generating diagrams from natural language descriptions
2. Managing diagram history and versions
3. Updating existing diagrams
4. Querying available syntax types and configurations

## Core Endpoints

### POST /diagrams/generate

Generates a diagram from a text description with optional code context.

**Request Body:**
```json
{
    "description": "Optional user description",
    "prompt": "The diagram prompt/description",
    "syntax_type": "mermaid",  // or "plantuml"
    "subtype": "auto",  // or specific type like "flowchart", "sequence", etc.
    "model": "optional model name",
    "options": {
        "agent": {
            "enabled": true,
            "max_iterations": 3
        },
        "rag": {
            "enabled": true,
            "api_doc_dir": "/path/to/code/context"
        }
    }
}
```

**Response:**
```json
{
    "code": "generated diagram code",
    "type": "mermaid",
    "subtype": "flowchart",
    "description": "user description",
    "prompt": "original prompt",
    "notes": ["generation notes"],
    "iterations": 2,
    "valid": true,
    "diagram_id": "unique-id",
    "conversation_id": "conversation-id"
}
```

### GET /diagrams/syntax-types

Get available diagram syntax types and their subtypes.

**Response:**
```json
{
    "syntax": ["mermaid", "plantuml"],
    "types": {
        "mermaid": ["flowchart", "sequence", "class", "state", "er", "mindmap"],
        "plantuml": ["sequence", "class", "usecase", "activity", "component"]
    }
}
```

### POST /diagrams/diagram/{id}/update

Update an existing diagram while preserving its structure.

**Request Body:**
```json
{
    "description": "Optional new description",
    "prompt": "Changes to apply",
    "syntax_type": "mermaid",
    "subtype": "auto",
    "model": "optional model name",
    "options": {
        "agent": {
            "enabled": true,
            "max_iterations": 3
        }
    }
}
```

**Response:**
```json
{
    "id": "diagram-id",
    "code": "updated diagram code",
    "type": "diagram type",
    "description": "updated description",
    "prompt": "update prompt",
    "createdAt": "timestamp",
    "metadata": {
        "iterations": 2,
        "valid": true
    },
    "notes": ["update notes"]
}
```

## History Management

### GET /diagrams/history

Get history of all generated diagrams.

**Response:**
```json
[
    {
        "id": "diagram-id",
        "description": "user description",
        "prompt": "generation prompt",
        "syntax": "mermaid",
        "createdAt": "timestamp",
        "iterations": 2
    }
]
```

### GET /diagrams/diagram/{id}

Get a specific diagram by ID.

**Response:**
```json
{
    "id": "diagram-id",
    "code": "diagram code",
    "type": "diagram type",
    "description": "user description",
    "prompt": "generation prompt", 
    "createdAt": "timestamp",
    "metadata": {
        "iterations": 2,
        "valid": true
    },
    "notes": []
}
```

### GET /diagrams/diagram/{id}/iterations

Get number of iterations for a specific diagram.

**Response:**
```json
2  // Number of iterations
```

### DELETE /diagrams/diagram/{id}

Delete a specific diagram.

**Response:**
```json
{
    "status": "success",
    "message": "Diagram {id} deleted successfully"
}
```

### DELETE /diagrams/clear

Clear all diagram history.

**Response:**
```json
{
    "status": "success",
    "message": "All diagrams deleted successfully (5 diagrams)",
    "state": {
        "diagrams_deleted": 5,
        "success": true
    }
}
```

## Error Handling

The API uses standard HTTP status codes:

- `400 Bad Request`: Invalid parameters or request body
- `404 Not Found`: Requested resource not found
- `500 Internal Server Error`: Server-side errors

Error responses include descriptive messages:

```json
{
    "detail": "Error description"
}
```

Common error scenarios:
1. Invalid diagram syntax type or subtype
2. Missing required parameters
3. RAG context directory not found
4. LLM generation failures
5. Invalid diagram ID for updates/queries
