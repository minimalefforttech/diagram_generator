"""Diagram agent for generating and refining diagram code."""

import json
import uuid
import logging
import re
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple, Any, Union

from pydantic import BaseModel, Field, ConfigDict, model_validator

from diagram_generator.backend.models.configs import AgentConfig, DiagramGenerationOptions
from diagram_generator.backend.models.ollama import OllamaAPI, ErrorResponse
from diagram_generator.backend.storage.database import Storage, DiagramRecord, ConversationRecord, ConversationMessage
from diagram_generator.backend.utils.rag import RAGProvider
from diagram_generator.backend.api.logs import log_error, log_llm
from diagram_generator.backend.utils.diagram_validator import DiagramValidator, ValidationResult, DiagramType

logger = logging.getLogger(__name__)

# Pydantic models for the agent
class DiagramAgentState(BaseModel):
    """Represents the state of the diagram agent."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    description: str = Field(..., description="Description of the diagram to generate")
    diagram_type: DiagramType = Field(..., description="Type of diagram to generate")
    code: Optional[str] = Field(None, description="Current diagram code")
    validation_result: Optional[Dict] = Field(None, description="Result of diagram validation")
    errors: List[str] = Field(default_factory=list, description="Current validation errors")
    iterations: int = Field(0, description="Number of iterations performed")
    context_section: str = Field("", description="RAG context to use in generation")
    notes: List[str] = Field(default_factory=list, description="Notes about the generation process")
    conversation_id: Optional[str] = Field(None, description="ID of the associated conversation")
    diagram_id: Optional[str] = Field(None, description="ID of the generated diagram")
    completed: bool = Field(False, description="Whether generation is complete")
    requirements: Dict[str, Any] = Field(default_factory=dict, description="Requirements determined from prompt")
    rag_provider: Optional[RAGProvider] = Field(None, description="RAG provider instance for context")
    current_activity: str = Field("Initializing", description="Current activity for loading indicator")

class DiagramAgentInput(BaseModel):
    """Input for the diagram agent."""
    description: str = Field(..., description="Description of the diagram to generate")
    diagram_type: str = Field("mermaid", description="Type of diagram to generate")
    options: Optional[DiagramGenerationOptions] = Field(None, description="Generation options")
    rag_context: Optional[str] = Field(None, description="RAG context to use in generation")

class DiagramAgentOutput(BaseModel):
    """Output from the diagram agent."""
    code: str = Field(..., description="Generated diagram code")
    diagram_type: str = Field(..., description="Type of diagram")
    notes: List[str] = Field(..., description="Notes about the generation process")
    valid: bool = Field(..., description="Whether the diagram is valid")
    iterations: int = Field(..., description="Number of iterations performed")
    diagram_id: Optional[str] = Field(None, description="ID of the generated diagram")
    conversation_id: Optional[str] = Field(None, description="ID of the associated conversation")

class DiagramAgent:
    """Agent responsible for generating and refining diagram code using tool-based approach."""

    PROMPT_TEMPLATES = {
        "generate": """Task: Create a {diagram_type} diagram.

Description: {description}

{context_section}

Example of a valid {diagram_type} diagram in {syntax_type}:
{example_code}

Rules:
1. Only output raw {diagram_type} code
2. No explanations, markdown formatting, code blocks, or backticks
3. Keep diagram simple and clear
4. Follow the syntax structure shown in the example above
{syntax_rules}

IMPORTANT: Your entire output must be valid {diagram_type} syntax that can be rendered directly.
""",
        "fix": """Task: Fix errors in {diagram_type} diagram.

Validation Errors:
{errors}

Current Code:
{code}

Rules:
1. Only output the fixed {diagram_type} code
2. No explanations or comments
3. Make minimal changes to fix errors
4. Ensure syntax is valid for rendering
5. Preserve all existing elements and connections

IMPORTANT: Return the complete diagram code with your changes."""
    }

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        default_model: str = "llama3.1:8b",
        storage: Optional[Storage] = None
    ):
        """Initialize DiagramAgent."""
        self.default_model = default_model
        self.storage = storage or Storage()
        self.ollama = OllamaAPI(base_url=base_url)
        self.logger = logging.getLogger(__name__)
        
    def _determine_requirements(
        self, 
        description: str, 
        diagram_type: DiagramType,
        rag_directory: Optional[str] = None,
        existing_diagram: Optional[str] = None
    ) -> Dict[str, Any]:
        """Analyze prompt and determine diagram requirements.
        
        Args:
            description: User's diagram description
            diagram_type: Type of diagram to generate (mermaid/plantuml)
            rag_directory: Optional directory path for RAG context
            existing_diagram: Optional existing diagram code to incorporate
            
        Returns:
            Dictionary containing determined requirements and context
        """
        requirements = {
            "description": description,
            "diagram_type": diagram_type,
            "existing_diagram": existing_diagram,
            "rag_context": None
        }
        
        # Load RAG context if directory provided
        if rag_directory:
            try:
                rag_provider = RAGProvider(
                    config=DiagramGenerationOptions().rag,
                    ollama_base_url=self.ollama.base_url
                )
                if rag_provider.load_docs_from_directory(rag_directory):
                    context = rag_provider.get_relevant_context(description)
                    if context:
                        requirements["rag_context"] = context
                        requirements["rag_provider"] = rag_provider
            except Exception as e:
                self.logger.error(f"Error loading RAG context: {str(e)}")
                
        return requirements
        
    def _strip_comments(self, code: str) -> str:
        """Remove comments, backticks and language specifiers from diagram code."""
        # Clean markdown code blocks
        if "```" in code:
            code = re.sub(r"```(?:mermaid|plantuml)?\s*([\s\S]+?)```", r"\1", code)
            
        # Remove comments for Mermaid
        lines = []
        for line in code.split("\n"):
            # Skip full-line comments
            if line.strip().startswith("%"):
                continue
            # Remove inline comments
            if "%" in line:
                line = line[:line.index("%")]
            lines.append(line)
            
        code = "\n".join(lines)
        
        # Remove any remaining backticks
        code = code.replace("`", "").strip()
        
        return code
        
    def _validate_mermaid(self, code: str) -> ValidationResult:
        """Validate Mermaid diagram syntax."""
        return DiagramValidator.validate(code, DiagramType.MERMAID)
        
    def _validate_plantuml(self, code: str) -> ValidationResult:
        """Validate PlantUML diagram syntax."""
        return DiagramValidator.validate(code, DiagramType.PLANTUML)

    def _get_syntax_rules(self, syntax_type: str) -> str:
        """Get syntax-specific rules based on the diagram type."""
        if syntax_type.lower() == 'mermaid':
            return """5. Additional Rules for Mermaid:
   - Use proper node and edge syntax
   - Apply styles with style statements
   - First line must match the diagram type from example"""
        else:  # plantuml
            return """5. Additional Rules for PlantUML:
   - Must start and end with the correct tags as shown in example
   - Use skinparam for styling
   - Follow the specific syntax for the diagram type"""

    def _detect_diagram_type(self, description: str) -> str:
        """Detect specific diagram type from description."""
        # Common diagram type keywords
        type_patterns = {
            'flowchart': ['flow', 'process', 'workflow', 'steps', 'flowchart'],
            'sequence': ['sequence', 'interaction', 'message', 'communication', 'flow between'],
            'class': ['class', 'object', 'inheritance', 'uml class', 'data model'],
            'state': ['state', 'status', 'transition', 'machine'],
            'er': ['entity', 'relationship', 'database', 'schema', 'data model'],
            'mindmap': ['mindmap', 'mind map', 'brainstorm', 'concept map', 'thought process'],
            'gantt': ['gantt', 'timeline', 'schedule', 'project plan', 'time'],
            'activity': ['activity', 'process flow', 'workflow steps'],
            'component': ['component', 'architecture', 'system', 'module'],
            'usecase': ['use case', 'user interaction', 'actor', 'system interaction']
        }
        
        description = description.lower()
        
        # Check for explicit type mentions first
        for diagram_type, keywords in type_patterns.items():
            if any(f"{keyword} diagram" in description for keyword in keywords):
                return diagram_type
                
        # Then check for implicit type hints
        for diagram_type, keywords in type_patterns.items():
            if any(keyword in description for keyword in keywords):
                return diagram_type
                
        # Default to flowchart if no specific type detected
        return 'flowchart'

    async def _generate_with_llm(
        self,
        description: str,
        diagram_type: str,
        context_section: str,
        agent_config: Optional[AgentConfig]
    ) -> Dict[str, str]:
        """Generate diagram using LLM."""
        # Detect specific diagram type from description
        specific_type = self._detect_diagram_type(description)
        
        # Get example code for the detected type
        from .diagram_examples import DiagramTypeExamples
        syntax_type = diagram_type.lower()  # mermaid or plantuml
        example_code = DiagramTypeExamples.get_example(specific_type, syntax_type)
        
        # Get syntax-specific rules
        syntax_rules = self._get_syntax_rules(syntax_type)

        prompt = self.PROMPT_TEMPLATES["generate"].format(
            description=description,
            diagram_type=specific_type,
            syntax_type=syntax_type,
            context_section=context_section,
            example_code=example_code,
            syntax_rules=syntax_rules
        )

        model = agent_config.model_name if agent_config and agent_config.enabled else self.default_model
        temperature = agent_config.temperature if agent_config and agent_config.enabled else 0.2
        system = agent_config.system_prompt if agent_config and agent_config.enabled else None

        try:
            log_llm("Starting LLM generation", {
                "model": model,
                "prompt": prompt,
                "temperature": temperature,
                "system": system
            })
            result = await self.ollama.generate(
                model=model,
                prompt=prompt,
                temperature=temperature,
                system=system
            )

            if isinstance(result, ErrorResponse):
                error_msg = f"Failed to generate diagram: {result.error}"
                log_error(error_msg)
                raise Exception(error_msg)

            # Ensure we have a response
            if not hasattr(result, 'response'):
                error_msg = "Invalid response format from LLM"
                log_error(error_msg)
                raise Exception(error_msg)

            # Get the raw content
            raw_content = result.response.strip()

            # Extract clean diagram code using various methods
            content = self._extract_clean_diagram_code(raw_content)

            # Ensure the content exists
            if not content:
                error_msg = "LLM returned empty or unusable response"
                log_error(error_msg)
                raise Exception(error_msg)

            log_llm("Generated diagram code successfully", {
                "content_length": len(content)
            })
            return {"content": content}
        except Exception as e:
            log_error(f"Error in _generate_with_llm: {str(e)}", exc_info=True)
            raise

    def _extract_clean_diagram_code(self, raw_content: str) -> str:
        """Extract clean diagram code from LLM response."""
        # Method 1: Extract content between backticks (```), prioritizing this approach
        if "```" in raw_content:
            try:
                # Extract all code blocks, including those with language specifiers
                code_blocks = re.findall(r"```(?:\w+)?\s*([\s\S]+?)```", raw_content)
                if code_blocks:
                    # Take the first code block that was found
                    return code_blocks[0].strip()
            except Exception as e:
                log_error(f"Error extracting code block: {str(e)}")
                
        # Method 2: Check for diagram code without backticks
        def is_valid_diagram_starter(line: str) -> bool:
            """Check if a line is a valid diagram starter."""
            line = line.lower().strip()
            # Mermaid starters
            if any(line.startswith(starter) for starter in [
                "graph ", "flowchart ", "sequencediagram", "classdiagram",
                "erdiagram", "mindmap", "gantt", "pie", "statediagram"
            ]):
                return True
            # PlantUML starters
            if any(starter in line for starter in [
                "@startuml", "@startmindmap", "@startgantt"
            ]):
                return True
            return False

        lines = raw_content.split('\n')
        start_idx = None
        end_idx = None

        # Find start of diagram code
        for i, line in enumerate(lines):
            if is_valid_diagram_starter(line):
                start_idx = i
                break

        if start_idx is not None:
            # Find end of diagram code
            for i in range(start_idx + 1, len(lines)):
                line = lines[i].lower().strip()
                # Stop conditions for finding the end of diagram code
                if (line.startswith(("here", "this diagram", "the diagram", "description:")) or
                    (line.startswith("@end") and i >= len(lines) - 1)):  # Allow @end if it's near the end
                    end_idx = i if not line.startswith("@end") else i + 1
                    break

            # If no explicit end was found, include all remaining lines
            if end_idx is None:
                end_idx = len(lines)

            return '\n'.join(lines[start_idx:end_idx]).strip()

        # Method 3: Clean and return the original content as a last resort
        return raw_content.replace("```mermaid", "").replace("```plantuml", "").replace("```", "").strip()

    def _init_state(self, input_data: DiagramAgentInput) -> DiagramAgentState:
        """Initialize agent state from input."""
        # Convert string diagram type to enum
        diagram_type = DiagramType(input_data.diagram_type.lower())

        return DiagramAgentState(
            description=input_data.description,
            diagram_type=diagram_type,
            context_section=input_data.rag_context or "",
            diagram_id=str(uuid.uuid4()),
            conversation_id=str(uuid.uuid4())
        )

    def _validate(self, state: DiagramAgentState) -> None:
        """Validate the current diagram."""
        if not state.code:
            state.validation_result = {"valid": False, "errors": ["No diagram code generated"]}
            state.errors = ["No diagram code generated"]
            return

        # Use DiagramValidator for validation
        validation_result = DiagramValidator.validate(state.code, state.diagram_type)

        # Convert ValidationResult to dict
        state.validation_result = validation_result.to_dict()
        state.errors = validation_result.errors

    def _store_results(self, state: DiagramAgentState) -> None:
        """Store the results in the database."""
        if not self.storage or not state.code:
            return

        now = datetime.now()

        # Store diagram
        diagram_record = DiagramRecord(
            id=state.diagram_id,
            description=state.description,
            diagram_type=state.diagram_type.value,
            code=state.code,
            created_at=now,
            tags=set(),
            metadata={
                "valid": not bool(state.errors),
                "iterations": state.iterations
            }
        )
        self.storage.save_diagram(diagram_record)

        # Store conversation
        messages = [ConversationMessage(
            role="user",
            content=state.description,
            timestamp=now,
            metadata={"type": "initial_request"}
        )]

        # Add generation message
        messages.append(ConversationMessage(
            role="assistant",
            content=state.code,
            timestamp=now,
            metadata={
                "type": "generation",
                "diagram_type": state.diagram_type.value
            }
        ))

        # Store conversation record
        conversation = ConversationRecord(
            id=state.conversation_id,
            diagram_id=state.diagram_id,
            messages=messages,
            created_at=now,
            updated_at=now,
            metadata={
                "context_section": state.context_section if state.context_section else None,
                "iterations": state.iterations,
                "errors": state.errors
            }
        )
        self.storage.save_conversation(conversation)

    def _prepare_output(self, state: DiagramAgentState) -> DiagramAgentOutput:
        """Prepare output from the final state."""
        return DiagramAgentOutput(
            code=state.code or "",
            diagram_type=state.diagram_type.value,
            notes=state.notes,
            valid=not bool(state.errors),
            iterations=state.iterations,
            diagram_id=state.diagram_id,
            conversation_id=state.conversation_id
        )

    async def generate_diagram(
        self,
        description: str,
        diagram_type: str = "mermaid",
        options: DiagramGenerationOptions = None,
        rag_provider: Optional[RAGProvider] = None,
    ) -> Tuple[str, List[str]]:
        """Generate a diagram with validation and fixing."""
        if not options:
            options = DiagramGenerationOptions()

        self.logger.info(f"Generating {diagram_type} diagram for: {description}")

        # Extract RAG directory from options
        rag_directory = options.rag.api_doc_dir if options.rag and options.rag.enabled else None
            
        # Create agent input and run
        input_data = DiagramAgentInput(
            description=description,
            diagram_type=diagram_type,
            options=options,
            rag_context=""  # We'll get context from _determine_requirements
        )

        # Run the agent
        output = await self.run_agent(input_data)

        return output.code, output.notes

    async def run_agent(self, input_data: DiagramAgentInput) -> DiagramAgentOutput:
        """Run the diagram agent to generate and validate a diagram."""
        # Initialize options if not provided
        options = input_data.options or DiagramGenerationOptions()

        # Initialize agent state
        state = self._init_state(input_data)

        # Extract RAG directory from options if present
        rag_directory = options.rag.api_doc_dir if options.rag and options.rag.enabled else None

        # Step 1: Determine requirements
        state.current_activity = "Analyzing Requirements"
        requirements = self._determine_requirements(
            state.description,
            state.diagram_type,
            rag_directory=rag_directory
        )
        state.requirements = requirements
        state.rag_provider = requirements.get("rag_provider")
        state.context_section = requirements.get("rag_context", "")

        # Step 2: Generate initial diagram
        state.current_activity = "Generating Diagram"
        try:
            result = await self._generate_with_llm(
                state.description,
                state.diagram_type.value,
                state.context_section,
                options.agent if options.agent.enabled else None
            )
            raw_code = result["content"]

            # Step 3: Strip comments
            state.current_activity = "Processing Code"
            state.code = self._strip_comments(raw_code)

            # Step 4: Validate
            state.current_activity = "Validating Diagram"
            if state.diagram_type == DiagramType.MERMAID:
                validation_result = self._validate_mermaid(state.code)
            else:
                validation_result = self._validate_plantuml(state.code)

            state.validation_result = validation_result.to_dict()
            state.errors = validation_result.errors

            # Track validation attempts
            attempts = 0
            while state.errors and attempts < options.agent.max_iterations:
                state.current_activity = f"Fixing Issues (Attempt {attempts + 1})"
                attempts += 1
                state.iterations += 1

                # Try to fix errors
                state.code = await self._fix_diagram(
                    state.code,
                    state.diagram_type.value,
                    state.errors,
                    options.agent
                )

                # Validate again
                state.current_activity = "Re-validating Diagram"
                if state.diagram_type == DiagramType.MERMAID:
                    validation_result = self._validate_mermaid(state.code)
                else:
                    validation_result = self._validate_plantuml(state.code)

                state.validation_result = validation_result.to_dict()
                state.errors = validation_result.errors

                if not state.errors:
                    state.notes.append("Successfully fixed diagram issues")
                    break
                else:
                    error_summary = ", ".join(state.errors[:2])
                    state.notes.append(f"Attempt {attempts}: Still fixing errors ({error_summary})")

            # Handle max iterations reached
            if state.errors and attempts >= options.agent.max_iterations:
                state.notes.append(f"Failed to generate valid diagram after {attempts} attempts")
                # We still return the code, but it will be shown in code editor view

        except Exception as e:
            state.notes.append(f"Error during generation: {str(e)}")
            state.errors.append(str(e))
            state.completed = True

        # Store results and cleanup
        state.current_activity = "Saving Results"
        self._store_results(state)
        state.completed = True

        return self._prepare_output(state)

    async def _fix_diagram(
        self,
        code: str,
        diagram_type: str,
        errors: List[str],
        config: Optional[AgentConfig] = None,
    ) -> str:
        """Fix diagram syntax errors."""
        # Detect diagram type from code structure
        from .diagram_examples import DiagramTypeExamples
        
        # Determine if it's mermaid or plantuml from the code
        syntax_type = 'plantuml' if '@startuml' in code or '@startmindmap' in code or '@startgantt' in code else 'mermaid'
        
        # Detect specific diagram type by examining first line or structure
        first_line = code.split('\n')[0].lower()
        if syntax_type == 'mermaid':
            if 'graph' in first_line or 'flowchart' in first_line:
                specific_type = 'flowchart'
            elif 'sequencediagram' in first_line:
                specific_type = 'sequence'
            elif 'classdiagram' in first_line:
                specific_type = 'class'
            elif 'statediagram' in first_line:
                specific_type = 'state'
            elif 'erdiagram' in first_line:
                specific_type = 'er'
            elif 'mindmap' in first_line:
                specific_type = 'mindmap'
            elif 'gantt' in first_line:
                specific_type = 'gantt'
            else:
                specific_type = 'flowchart'  # default
        else:  # plantuml
            if '@startmindmap' in first_line:
                specific_type = 'mindmap'
            elif '@startgantt' in first_line:
                specific_type = 'gantt'
            elif 'class' in code.lower():
                specific_type = 'class'
            elif 'state' in code.lower():
                specific_type = 'state'
            elif 'actor' in code.lower() or 'usecase' in code.lower():
                specific_type = 'usecase'
            elif 'component' in code.lower():
                specific_type = 'component'
            elif 'entity' in code.lower():
                specific_type = 'er'
            elif 'participant' in code.lower() or '->' in code:
                specific_type = 'sequence'
            elif 'activity' in code.lower():
                specific_type = 'activity'
            else:
                specific_type = 'sequence'  # default
        
        # Get example code for the detected type
        example_code = DiagramTypeExamples.get_example(specific_type, syntax_type)
        
        prompt = self.PROMPT_TEMPLATES["fix"].format(
            diagram_type=specific_type,
            code=code,
            errors="\n".join(errors)
        )

        model = config.model_name if config and config.enabled else self.default_model
        temperature = config.temperature if config and config.enabled else 0.2

        # Add example code to system prompt
        system_prompt = f"""Use this example as a reference for valid syntax:

{example_code}

When fixing the diagram:
1. Keep the same type of nodes, edges, and relationships as the original
2. Ensure syntax matches the example above
3. Maintain the same diagram elements but fix their syntax
"""

        # Override with config system prompt if provided
        system = config.system_prompt if config and config.enabled and config.system_prompt else system_prompt

        try:
            result = await self.ollama.generate(
                model=model,
                prompt=prompt,
                temperature=temperature,
                system=system
            )

            if isinstance(result, ErrorResponse):
                error_msg = f"Failed to fix diagram: {result.error}"
                log_error(error_msg)
                raise Exception(error_msg)

            if not hasattr(result, 'response'):
                error_msg = "Invalid response format from LLM"
                log_error(error_msg)
                raise Exception(error_msg)

            fixed_code = result.response.strip()
            if not fixed_code:
                error_msg = "Fix resulted in empty diagram"
                log_error(error_msg)
                raise Exception(error_msg)

            log_llm("Applied fix to diagram", {
                "content_length": len(fixed_code),
                "diagram": fixed_code
            })

            return fixed_code
        except Exception as e:
            self.logger.error(f"Error in fix_diagram: {str(e)}", exc_info=True)
            raise
