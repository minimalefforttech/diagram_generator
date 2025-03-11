# API Reference

This document describes the publicly exposed API endpoints for diagram generation, validation, and conversion.

## Table of Contents

1. [Introduction](#introduction)
2. [Endpoints](#endpoints)
   - [POST /diagrams/generate](#1-post-diagramsgenerate)
   - [POST /diagrams/validate](#2-post-diagramsvalidate)
   - [POST /diagrams/convert](#3-post-diagramsconvert)
3. [Example Usage](#example-usage)
4. [Error Handling](#error-handling)
5. [Future Enhancements](#future-enhancements)

## Introduction

The system uses FastAPI to expose several endpoints under the "/diagrams" route so that users can:
1. Generate diagrams by providing a natural language description.
2. Validate existing diagram code.
3. Convert diagram code between different diagram syntax types (e.g., Mermaid, PlantUML, etc.).

## Endpoints

### 1. POST /diagrams/generate

Generates a diagram from a text description.

**URL:**  
`POST /diagrams/generate`
  
**Query Parameters:**
- `description` (string, required): The textual description of the diagram to be generated
- `diagram_type` (string, optional): The target diagram syntax (default: "mermaid")
- `options` (object, optional): Additional generation parameters

**Response Body (JSON):**
```json
{
    "diagram": "<diagram_code>",
    "type": "<type_of_diagram_syntax>",
    "notes": ["<any_additional_notes_or_warnings>"]
}
```

**Example cURL request:**
```bash
curl -X POST "http://localhost:8000/diagrams/generate?description=Create+a+simple+flowchart+with+two+nodes:+Start+and+End"
```

**Example PowerShell request:**
```powershell
Invoke-WebRequest -Method POST -Uri "http://localhost:8000/diagrams/generate?description=Create+a+simple+flowchart+with+two+nodes:+Start+and+End"
```

### 2. POST /diagrams/validate

Validates the syntax of the provided diagram code.

**URL:**  
`POST /diagrams/validate`

**Query Parameters:**
- `code` (string, required): The diagram code to validate
- `diagram_type` (string, optional): The syntax type of the diagram (default: "mermaid")

**Response Body (JSON):**
```json
{
    "valid": true | false,
    "errors": [],
    "suggestions": []
}
```

**Example cURL request:**
```bash
curl -X POST "http://localhost:8000/diagrams/validate?diagram_type=mermaid" \
     -H "Content-Type: application/json" \
     --data '{"code":"graph LR;\nA-->B;"}'
```

### 3. POST /diagrams/convert

Converts diagram code from one syntax type to another.

**URL:**  
`POST /diagrams/convert`

**Query Parameters:**
- `diagram` (string, required): The diagram code to convert
- `source_type` (string, required): The syntax type of the diagram code provided
- `target_type` (string, required): The desired syntax type for the converted diagram

**Response Body (JSON):**
```json
{
    "diagram": "<converted_diagram_code>",
    "source_type": "<source_type>",
    "target_type": "<target_type>",
    "notes": []
}
```

**Example cURL request:**
```bash
curl -X POST "http://localhost:8000/diagrams/convert?source_type=mermaid&target_type=plantuml" \
     -H "Content-Type: application/json" \
     --data '{"diagram":"graph LR;\nA-->B;"}'
```

## Example Usage

Below are some example commands using PowerShell to demonstrate requests:

1) Generate a flowchart (Mermaid):
```powershell
Invoke-WebRequest -Method POST -Uri "http://localhost:8000/diagrams/generate?description=Create+a+simple+flowchart+with+two+nodes:+Start+and+End" | Select-Object -ExpandProperty Content
```

2) Validate a snippet of Mermaid code:
```powershell
$jsonResponse = Invoke-WebRequest -Method POST -Uri "http://localhost:8000/diagrams/validate?diagram_type=mermaid" `
    -Body '{"code":"graph LR; A-->B;"}' `
    -ContentType "application/json" |
    Select-Object -ExpandProperty Content

Write-Host $jsonResponse
```

3) Convert a Mermaid diagram to PlantUML:
```powershell
$jsonResponse = Invoke-WebRequest -Method POST -Uri "http://localhost:8000/diagrams/convert?source_type=mermaid&target_type=plantuml" `
    -Body '{"diagram":"graph LR; A-->B;"}' `
    -ContentType "application/json" |
    Select-Object -ExpandProperty Content

Write-Host $jsonResponse
```

## Error Handling

Status Codes:
- `400 Bad Request`: Missing or invalid parameters
- `500 Internal Server Error`: Server-side errors or LLM service failures

Common error scenarios:
1. Missing required parameters
2. Invalid diagram syntax
3. LLM service unavailable
4. Conversion between incompatible diagram types

## Future Enhancements

1. **Additional Diagram Types**
   - Support for PlantUML
   - Support for Graphviz/DOT
   - UML class diagrams
   - Entity-Relationship diagrams

2. **Authentication & Authorization**
   - API key authentication
   - Rate limiting
   - User-specific quotas

3. **Storage & History**
   - Save generated diagrams
   - Version control
   - Diagram sharing

4. **Enhanced Validation**
   - Syntax-specific validators
   - Style checkers
   - Best practice recommendations
