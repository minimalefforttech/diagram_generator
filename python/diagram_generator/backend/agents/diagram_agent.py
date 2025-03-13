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
from diagram_generator.backend.utils.caching import DiagramCache
from diagram_generator.backend.utils.rag import RAGProvider
from diagram_generator.backend.utils.diagram_validator import DiagramValidator, ValidationResult, DiagramType

logger = logging.getLogger(__name__)

# New Pydantic models for the agent
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
3. Keep diagram simple (2-3 nodes with basic connections)
4. Start directly with valid {diagram_type} syntax
5. If colors are specified, apply them correctly using {diagram_type} styling syntax

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
6. If this is a styling request, DO NOT change the diagram structure

For styling in Mermaid diagrams:
- Add style statements at the end of the diagram
- Example: style NodeA fill:#1976d2,stroke:#333,color:#fff
- Example: linkStyle 0 stroke:#d32f2f,stroke-width:2px
- Example: classDef default fill:#388e3c,stroke:#333,color:#fff
- Match node IDs exactly as they appear in the diagram

IMPORTANT: Return the complete diagram code with your changes.
"""
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

Never generate a new diagram. Only style the existing one.
"""
    }

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        default_model: str = "llama3.1:8b",
        cache_dir: str = ".cache/diagrams",
        cache_ttl: Optional[float] = 3600,  # 1 hour default TTL
        storage: Optional[Storage] = None
    ):
        """Initialize DiagramAgent."""
        self.default_model = default_model
        self.cache_ttl = cache_ttl
        self.cache = DiagramCache(cache_dir=cache_dir)
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
            result = await self.ollama.generate(
                model=model,
                prompt=prompt,
                temperature=temperature,
                system=system
            )
            
            if isinstance(result, ErrorResponse):
                logger.error(f"LLM generation error: {result.error}")
                raise Exception(f"Failed to generate diagram: {result.error}")
                
            # Ensure we have a response
            if not hasattr(result, 'response'):
                logger.error("Invalid response format from LLM")
                raise Exception("Invalid response format from LLM")
                
            # Get the raw content
            raw_content = result.response.strip()
            
            # Extract clean diagram code using various methods
            content = self._extract_clean_diagram_code(raw_content)
                
            # Ensure the content exists
            if not content:
                logger.error("LLM returned empty or unusable response")
                raise Exception("Empty or unusable response from LLM")
                
            return {"content": content}
        except Exception as e:
            logger.error(f"Error in _generate_with_llm: {str(e)}", exc_info=True)
            raise
            
    def _extract_clean_diagram_code(self, raw_content: str) -> str:
        """Extract clean diagram code from LLM response, removing explanatory text."""
        # Method 1: Check for markdown code blocks
        if "```" in raw_content:
            try:
                # Extract content between triple backticks
                code_block_pattern = r"```(?:mermaid)?\s*([\s\S]+?)```"
                matches = re.findall(code_block_pattern, raw_content)
                if matches:
                    return matches[0].strip()
            except Exception as e:
                self.logger.warning(f"Error extracting code block: {str(e)}")
        
        # Method 2: Look for known diagram syntax starters
        lines = raw_content.split("\n")
        for i, line in enumerate(lines):
            line_lower = line.lower().strip()
            if (line_lower.startswith("graph ") or 
                line_lower.startswith("flowchart ") or 
                line_lower.startswith("sequencediagram") or 
                line_lower.startswith("classDiagram")):
                
                # Found a diagram starter, now find where it ends
                diagram_lines = []
                for j in range(i, len(lines)):
                    current = lines[j]
                    # Stop if we hit explanatory text
                    if (current.strip().lower().startswith("this diagram") or
                        current.strip().lower().startswith("the diagram") or
                        current.strip().lower().startswith("here is") or
                        current.strip().lower().startswith("description:")):
                        break
                    diagram_lines.append(current)
                
                if diagram_lines:
                    return "\n".join(diagram_lines)
        
        # Method 3: If all else fails, remove obvious explanatory text blocks at the end
        parts = re.split(r"\n\s*\n", raw_content)  # Split by blank lines
        if len(parts) > 1:
            # Check if the last part looks like explanatory text
            last_part = parts[-1].strip().lower()
            if (last_part.startswith("this diagram") or
                last_part.startswith("the diagram") or
                last_part.startswith("description:") or
                last_part.startswith("here is")):
                return "\n".join(parts[:-1]).strip()
        
        # Just return the original content if we couldn't identify explanatory text
        return raw_content.replace("```mermaid", "").replace("```", "").strip()

    # New agent lifecycle methods
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
            
        # Check cache first
        context_section = ""
        if rag_provider and options.rag.enabled:
            context = rag_provider.get_relevant_context(description)
            if context:
                context_section = f"Use this API context:\n{context}\n\n"
                
        cache_entry = self.cache.get(
            description=description,
            diagram_type=diagram_type,
            rag_context=context_section if context_section else None
        )
        
        if cache_entry:
            self.logger.info("Using cached diagram")
            return cache_entry.value, ["Using cached diagram"]
            
        # Create agent input
        input_data = DiagramAgentInput(
            description=description,
            diagram_type=diagram_type,
            options=options,
            rag_context=context_section
        )
        
        # Run the agent
        output = await self.run_agent(input_data)
        
        # Cache successful generation
        if output.valid:
            self.cache.set(
                description=description,
                diagram_type=diagram_type,
                value=output.code,
                ttl=self.cache_ttl,
                rag_context=context_section if context_section else None
            )
        
        return output.code, output.notes

    async def run_agent(self, input_data: DiagramAgentInput) -> DiagramAgentOutput:
        """Run the diagram agent to generate and validate a diagram."""
        # Initialize options if not provided
        options = input_data.options or DiagramGenerationOptions()
        
        # Initialize agent state
        state = self._init_state(input_data)
        
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
                self.logger.error(f"Fix error: {result.error}")
                raise Exception(f"Failed to fix diagram: {result.error}")
                
            if not hasattr(result, 'response'):
                self.logger.error("Invalid response format from LLM")
                raise Exception("Invalid response format from LLM")
                
            fixed_code = result.response.strip()
            if not fixed_code:
                self.logger.error("Fix resulted in empty diagram")
                raise Exception("Fix resulted in empty diagram")
                
            return fixed_code
        except Exception as e:
            self.logger.error(f"Error in fix_diagram: {str(e)}", exc_info=True)
            raise
