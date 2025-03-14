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
    """Agent responsible for generating and refining diagram code."""

    PROMPT_TEMPLATES = {
        "generate": """Task: Create a {diagram_type} diagram.

Description: {description}

{context_section}
Rules:
1. Only output raw {diagram_type} code
2. No explanations, markdown formatting, code blocks, or backticks
3. Keep diagram simple and clear
4. Start directly with valid {diagram_type} syntax
5. For Mermaid diagrams:
   - Use proper node and edge syntax
   - Apply styles with style statements
   - First line must be the diagram type: [graph TD, sequenceDiagram, gantt, pie, classDiagram, stateDiagram, erDiagram, journey, mindmap, quadrantChart]
6. For PlantUML diagrams:
   - Must start with the correct tag:
     * For mindmaps: @startmindmap
     * For Gantt: @startgantt
     * For class diagrams: @startuml with class syntax
     * For sequence diagrams: @startuml with sequence syntax
     * For state diagrams: @startuml with state syntax
     * For activity diagrams: @startuml with activity syntax
     * For component diagrams: @startuml with component syntax
     * For deployment diagrams: @startuml with deployment syntax
     * For object diagrams: @startuml with object syntax
     * For use case diagrams: @startuml with usecase syntax
     * For ER diagrams: @startuml with entity-relationship syntax
     * For timing diagrams: @startuml with timing syntax
   - Must end with @enduml
   - Use skinparam for styling

IMPORTANT: Your entire output must be valid {diagram_type} syntax that can be rendered directly.
""",
        "fix": """Task: Fix errors in {diagram_type} diagram or apply styling changes.

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
6. For Mermaid styling:
   - Add style statements at the end
   - Use proper style syntax for nodes and edges
7. For PlantUML styling:
   - Use skinparam commands at the start
   - Use proper color/style attributes

IMPORTANT: Return the complete diagram code with your changes."""
    }

    # System prompts for different tasks
    SYSTEM_PROMPTS = {
        "styling": """You are a specialized diagram styling agent. You modify diagram styling without changing the structure.
When given a diagram and styling instructions:
1. Always preserve the original diagram structure and content
2. Only add or modify style statements
3. Keep all nodes, connections, and text from the original diagram
4. Apply styles precisely as requested
5. Return the complete diagram with styling applied

For Mermaid diagrams, use appropriate styling syntax:
- Node styling: style NodeName fill:#colorcode,stroke:#colorcode,color:#textcolor
- Edge styling: linkStyle 0 stroke:#colorcode,stroke-width:2px
- Class styling: classDef className fill:#colorcode,stroke:#colorcode,color:#textcolor

For PlantUML diagrams, use appropriate styling syntax:
- Global styles: skinparam monochrome true
- Component styles: skinparam component { BackgroundColor #colorcode, BorderColor #colorcode }
- Arrow styles: skinparam arrow { Color #colorcode, Thickness 2 }

Never generate a new diagram. Only style the existing one.
"""
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

    async def _generate_with_llm(
        self,
        description: str,
        diagram_type: str,
        context_section: str,
        agent_config: Optional[AgentConfig]
    ) -> Dict[str, str]:
        """Generate diagram using LLM."""
        prompt = self.PROMPT_TEMPLATES["generate"].format(
            description=description,
            diagram_type=diagram_type,
            context_section=context_section
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

        def extract_from_code_block(block: str) -> str:
            """Extract and validate diagram code from a code block."""
            lines = block.strip().split('\n')
            # Skip any explanatory text before the actual diagram code
            for i, line in enumerate(lines):
                if is_valid_diagram_starter(line):
                    return '\n'.join(lines[i:])
            return block

        # Method 1: Handle code blocks first
        if "```" in raw_content:
            try:
                # Extract all code blocks including with language specifiers
                code_blocks = re.findall(r"```(?:mermaid|plantuml)?\s*([\s\S]+?)```", raw_content)
                if code_blocks:
                    # Process each code block and keep the first valid one
                    for block in code_blocks:
                        cleaned = extract_from_code_block(block.strip())
                        if is_valid_diagram_starter(cleaned.split('\n')[0]):
                            return cleaned
            except Exception as e:
                log_error(f"Error extracting code block: {str(e)}")

        # Method 2: Look for diagram code without code blocks
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

    async def _plan(self, state: DiagramAgentState, options: DiagramGenerationOptions) -> None:
        """Plan the next action based on current state."""
        # If we don't have diagram code yet, plan to generate it
        if not state.code:
            state.notes.append("Planning initial diagram generation")
            return

        # If we've reached max iterations or diagram is valid, plan to complete
        if state.iterations >= options.agent.max_iterations:
            state.notes.append(f"Reached maximum iterations ({options.agent.max_iterations})")
            state.completed = True
            return

        if state.validation_result and state.validation_result.get("valid", False):
            state.notes.append("Diagram validation successful")
            state.completed = True
            return

        # Otherwise plan to fix errors
        state.notes.append(f"Planning iteration {state.iterations + 1} to fix errors")

    async def _execute(self, state: DiagramAgentState, options: DiagramGenerationOptions) -> None:
        """Execute the current plan."""
        # Generate new diagram if we don't have one yet
        if not state.code:
            try:
                result = await self._generate_with_llm(
                    state.description,
                    state.diagram_type.value,
                    state.context_section,
                    options.agent if options and options.agent.enabled else None
                )
                state.code = result["content"]
                state.notes.append("Generated initial diagram")
            except Exception as e:
                state.notes.append(f"Error generating diagram: {str(e)}")
                state.errors.append(f"Generation failed: {str(e)}")
                state.completed = True
            return

        # Otherwise, try to fix errors
        if state.errors:
            try:
                state.code = await self._fix_diagram(
                    state.code,
                    state.diagram_type.value,
                    state.errors,
                    options.agent
                )
                state.notes.append(f"Applied fixes in iteration {state.iterations + 1}")
                state.iterations += 1
            except Exception as e:
                state.notes.append(f"Error fixing diagram: {str(e)}")
                state.errors.append(f"Fix attempt failed: {str(e)}")
                state.completed = True

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

        # Get RAG context if enabled
        context_section = ""
        if rag_provider and options.rag.enabled:
            context = rag_provider.get_relevant_context(description)
            if context:
                context_section = f"Use this API context:\n{context}\n\n"

        # Create agent input
        input_data = DiagramAgentInput(
            description=description,
            diagram_type=diagram_type,
            options=options,
            rag_context=context_section
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

        # Track consecutive validation failures
        consecutive_failures = 0
        max_consecutive_failures = 3

        # Agent loop
        while not state.completed:
            # Plan what to do next
            await self._plan(state, options)

            # If completed during planning, exit loop
            if state.completed:
                break

            # Execute the plan
            await self._execute(state, options)

            # Validate the result
            self._validate(state)

            # Check validation result
            if state.validation_result:
                if state.validation_result.get("valid", False):
                    # Success - diagram is valid
                    state.notes.append("Generated valid diagram")
                    state.completed = True
                else:
                    # Track consecutive failures
                    consecutive_failures += 1
                    if consecutive_failures >= max_consecutive_failures:
                        state.notes.append(f"Failed to generate valid diagram after {consecutive_failures} attempts")
                        break
                    elif state.iterations >= options.agent.max_iterations:
                        state.notes.append(f"Reached maximum iterations ({options.agent.max_iterations})")
                        break
                    else:
                        # Prepare for next iteration
                        state.iterations += 1
                        error_summary = ", ".join(state.errors[:2])  # First few errors
                        state.notes.append(f"Attempt {state.iterations}: Fixing errors ({error_summary})")

        # Store results
        self._store_results(state)

        # Return output
        return self._prepare_output(state)

    async def _fix_diagram(
        self,
        code: str,
        diagram_type: str,
        errors: List[str],
        config: Optional[AgentConfig] = None,
    ) -> str:
        """Fix diagram syntax errors."""
        prompt = self.PROMPT_TEMPLATES["fix"].format(
            diagram_type=diagram_type,
            code=code,
            errors="\n".join(errors)
        )

        model = config.model_name if config and config.enabled else self.default_model
        temperature = config.temperature if config and config.enabled else 0.2

        # Check if this is a styling request to use specialized system prompt
        is_styling_request = any(styling_term in " ".join(errors).lower() for styling_term in 
                               ["style", "color", "fill", "stroke", "theme", "styling", "appearance"])

        # Use styling system prompt for color/styling requests
        system = self.SYSTEM_PROMPTS["styling"] if is_styling_request else None
        system = config.system_prompt if config and config.enabled and config.system_prompt else system

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

            log_llm("Fixed diagram successfully", {
                "content_length": len(fixed_code)
            })

            return fixed_code
        except Exception as e:
            self.logger.error(f"Error in fix_diagram: {str(e)}", exc_info=True)
            raise
