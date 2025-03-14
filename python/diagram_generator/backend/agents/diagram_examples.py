"""Examples for each diagram type to ensure valid syntax."""

from enum import Enum

class DiagramTypeExamples:
    """Contains example diagrams for each type to help ensure valid syntax."""
    
    # Mermaid examples
    MERMAID_EXAMPLES = {
        "flowchart": """graph TD
    A[Start] --> B[Process]
    B --> C{Decision?}
    C -->|Yes| D[Action 1]
    C -->|No| E[Action 2]
    D --> F[End]
    E --> F""",

        "sequence": """sequenceDiagram
    participant User
    participant System
    User->>System: Request
    System->>Database: Query
    Database-->>System: Response
    System-->>User: Result""",

        "class": """classDiagram
    class Animal {
        +String name
        +makeSound()
    }
    class Dog {
        +breed: String
        +bark()
    }
    Animal <|-- Dog""",

        "state": """stateDiagram-v2
    [*] --> Idle
    Idle --> Processing: Start
    Processing --> Done: Complete
    Processing --> Error: Fail
    Done --> [*]
    Error --> Idle: Retry""",

        "er": """erDiagram
    CUSTOMER ||--o{ ORDER : places
    ORDER ||--|{ LINE_ITEM : contains
    CUSTOMER {
        string name
        string email
    }
    ORDER {
        int id
        date created_at
    }""",

        "mindmap": """mindmap
  root((Project))
    Features
      Core
      Advanced
    Timeline
      Phase 1
      Phase 2
    Resources
      Team
      Budget""",
        
        "gantt": """gantt
    title Project Timeline
    dateFormat  YYYY-MM-DD
    section Planning
    Task 1           :a1, 2024-01-01, 7d
    Task 2           :a2, after a1, 5d
    section Development
    Task 3           :a3, after a2, 10d"""
    }

    # PlantUML examples
    PLANTUML_EXAMPLES = {
        "sequence": """@startuml
participant User
participant System
participant Database

User -> System: Request
System -> Database: Query
Database --> System: Response
System --> User: Result
@enduml""",

        "class": """@startuml
class Animal {
  +name: String
  +makeSound()
}
class Dog {
  +breed: String
  +bark()
}
Animal <|-- Dog
@enduml""",

        "state": """@startuml
[*] --> Idle
Idle --> Processing: Start
Processing --> Done: Complete
Processing --> Error: Fail
Done --> [*]
Error --> Idle: Retry
@enduml""",

        "activity": """@startuml
start
:Initialize;
if (Valid?) then (yes)
  :Process Data;
  :Save Results;
else (no)
  :Handle Error;
endif
stop
@enduml""",

        "component": """@startuml
package "Frontend" {
  [UI Components]
  [Router]
}
package "Backend" {
  [API Server]
  [Database]
}
[UI Components] --> [API Server]
[API Server] --> [Database]
@enduml""",

        "usecase": """@startuml
left to right direction
actor User
rectangle System {
  usecase "Login" as UC1
  usecase "View Data" as UC2
  usecase "Update Profile" as UC3
}
User --> UC1
User --> UC2
User --> UC3
@enduml""",

        "er": """@startuml
entity Customer {
  * id: number
  --
  * name: string
  * email: string
}

entity Order {
  * id: number
  --
  * customer_id: number
  * created_at: date
}

Customer ||--|{ Order
@enduml""",

        "mindmap": """@startmindmap
* Project
** Features
*** Core
*** Advanced
** Timeline
*** Phase 1
*** Phase 2
** Resources
*** Team
*** Budget
@endmindmap""",

        "gantt": """@startgantt
[Task 1] lasts 7 days
then [Task 2] lasts 5 days
then [Task 3] lasts 10 days
@endgantt"""
    }

    @staticmethod
    def get_example(diagram_type: str, syntax_type: str) -> str:
        """Get example diagram code for the specified type and syntax.
        
        Args:
            diagram_type: Type of diagram (flowchart, sequence, class, etc)
            syntax_type: Either 'mermaid' or 'plantuml'
            
        Returns:
            Example diagram code as string
        """
        examples = (DiagramTypeExamples.MERMAID_EXAMPLES 
                   if syntax_type.lower() == 'mermaid' 
                   else DiagramTypeExamples.PLANTUML_EXAMPLES)
        
        # Map some common diagram type variations
        type_mapping = {
            'graph': 'flowchart',
            'flow': 'flowchart',
            'flowchart': 'flowchart',
            'sequence': 'sequence',
            'class': 'class',
            'state': 'state',
            'er': 'er',
            'mindmap': 'mindmap',
            'gantt': 'gantt',
            'activity': 'activity',
            'component': 'component',
            'usecase': 'usecase'
        }
        
        normalized_type = type_mapping.get(diagram_type.lower(), diagram_type.lower())
        return examples.get(normalized_type, examples['flowchart'])
