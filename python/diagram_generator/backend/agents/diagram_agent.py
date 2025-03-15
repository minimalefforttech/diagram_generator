"""Diagram agent for generating and refining diagram code."""

import json
import uuid
import logging
import re
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple, Any, Union
import os  # Add import for file operations

from pydantic import BaseModel, Field, ConfigDict, model_validator

from diagram_generator.backend.models.configs import AgentConfig, DiagramGenerationOptions
from diagram_generator.backend.models.ollama import OllamaAPI, ErrorResponse
from diagram_generator.backend.storage.database import Storage, DiagramRecord, ConversationRecord, ConversationMessage
from diagram_generator.backend.utils.rag import RAGProvider
from diagram_generator.backend.api.logs import log_error, log_llm, log_info
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
        "generate": """Task: Create a {diagram_type} diagram based on the provided code context.

Description: {description}

CODE CONTEXT (IMPORTANT - USE THIS TO CREATE YOUR DIAGRAM):
{context_section}

Rules:
1. Output ONLY valid {diagram_type} diagram code in {syntax_type} syntax
2. Keep the diagram type exactly as specified ({diagram_type})
{example_section}
3. Your diagram MUST accurately represent the provided code context
4. Include all important classes, methods, and relationships from the context
5. Preserve indentation and structure exactly
6. Do not convert to a different diagram type
7. No explanations, markdown formatting, or backticks
{syntax_rules}

CRITICAL: 
- USE THE CODE CONTEXT to create an accurate diagram of the system
- Your response must be ONLY valid {diagram_type} code in the exact format shown above
- DO NOT convert mindmap to flowchart or change the diagram type in any way
""",
        "fix": """Task: Fix errors in {diagram_type} diagram while preserving exact type and structure.

Current Code to Fix:
{code}

Validation Errors to Address:
{errors}

Rules:
1. Keep EXACTLY the same diagram type ({diagram_type})
2. Preserve indentation and structure exactly
3. Only fix the specific validation errors
4. Do not convert or modify the diagram type
5. Keep all existing elements and connections
6. No explanations or comments in the output

CRITICAL: Your response must be ONLY the fixed {diagram_type} code.
DO NOT modify the diagram type or convert to a different format.
Preserve the exact structure while only fixing the validation errors."""
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

    async def _determine_requirements(
        self, 
        description: str, 
        diagram_type: DiagramType,
        rag_directory: Optional[str] = None,
        existing_diagram: Optional[str] = None
    ) -> Dict[str, Any]:
        """Analyze prompt and determine diagram requirements."""
        requirements = {
            "description": description,
            "diagram_type": diagram_type,
            "existing_diagram": existing_diagram,
            "rag_context": None
        }
        
        # Load RAG context if directory provided
        if rag_directory:
            try:
                log_info(f"Setting up RAG with directory: {rag_directory}")
                rag_config = DiagramGenerationOptions().rag
                rag_config.api_doc_dir = rag_directory
                rag_config.enabled = True
                
                # Ensure RAG config has necessary attributes
                if not hasattr(rag_config, 'similarity_threshold'):
                    log_info("Adding default similarity_threshold to RAG config")
                    # Don't modify the config object directly, we'll let RAGProvider handle defaults
                    
                rag_provider = RAGProvider(
                    config=rag_config,
                    ollama_base_url=self.ollama.base_url
                )
                
                # Get relevant context from code (modified to support async call)
                success = await rag_provider.load_docs_from_directory(rag_directory, use_simple_file_splitting=True)
                
                if success:
                    log_info(f"RAG Provider Stats: {rag_provider.stats.model_dump_json(indent=2)}")
                    # Enhance query with diagram specific terms to improve context retrieval
                    enhanced_query = self._enhance_query_for_diagram(description, diagram_type)
                    log_info(f"Enhanced RAG query: {enhanced_query}")
                    
                    # Get file overview to help with context
                    file_overview = self._get_directory_overview(rag_directory)
                    if file_overview:
                        log_info("Including directory structure overview in RAG context")
                        enhanced_query += "\n\nAvailable files:\n" + file_overview
                    
                    search_result = await rag_provider.get_relevant_context(enhanced_query)
                    if search_result and search_result.documents:
                        log_info(
                            f"Found {len(search_result.documents)} relevant documents for query"
                        )
                        context_parts = []
                        for i, doc in enumerate(search_result.documents):
                            # Check if this is an EmbeddedDocument with score
                            if hasattr(doc, 'score'):
                                log_info(f"Document {i+1} relevance score: {doc.score}")
                            else:
                                # If it's just a regular Document without score, don't try to log the score
                                log_info(f"Document {i+1} from {doc.metadata.source}")
                            context_parts.append(f"--- {doc.metadata.source} ---\n{doc.content}")
                        
                        context_text = "\n\n".join(context_parts)
                        requirements["rag_context"] = context_text
                        requirements["rag_provider"] = rag_provider
                        
                        # Log the first part of the context to verify content
                        preview = context_text[:500] + "..." if len(context_text) > 500 else context_text
                        log_info(f"RAG context preview: {preview}")
                    else:
                        self.logger.warning("No relevant context found in documents")
                else:
                    self.logger.error("Failed to load documents for RAG")
            except Exception as e:
                self.logger.error(f"Error setting up RAG: {str(e)}", exc_info=True)
                
        return requirements
    
    def _get_directory_overview(self, directory: str) -> str:
        """Get a simple overview of the directory structure to provide additional context."""
        try:
            file_paths = []
            for root, _, files in os.walk(directory):
                for file in files:
                    # Only include code files
                    if file.endswith(('.py', '.js', '.ts', '.jsx', '.tsx', '.html', '.css', 
                                     '.java', '.c', '.cpp', '.cs', '.go', '.rs', '.php')):
                        rel_path = os.path.relpath(os.path.join(root, file), directory)
                        file_paths.append(rel_path)
            
            # Sort and return as a simple list
            file_paths.sort()
            return "\n".join(file_paths[:50])  # Limit to 50 files to avoid overwhelming
        except Exception as e:
            self.logger.error(f"Error getting directory overview: {str(e)}")
            return ""

    def _enhance_query_for_diagram(self, description: str, diagram_type: DiagramType) -> str:
        """Enhance the search query with diagram-specific terms to improve context retrieval."""
        diagram_type_str = diagram_type.value
        
        # Add diagram-specific search terms based on the type
        if diagram_type == DiagramType.MERMAID:
            specific_type = self._detect_diagram_type(description)
            
            if specific_type == 'class':
                return f"{description} class definition interface extends implements"
            elif specific_type == 'flowchart':
                return f"{description} function process workflow steps"
            elif specific_type == 'sequence':
                return f"{description} function calls API endpoints interactions"
            elif specific_type == 'er':
                return f"{description} database schema entity model relationship"
            elif specific_type == 'component':
                return f"{description} component module service architecture"
            else:
                return f"{description} structure diagram {specific_type}"
        else:
            # PlantUML specific enhancements
            return f"{description} UML class definition interface relationship"
        
    def _strip_comments(self, code: str) -> str:
        """Remove comments and markdown formatting without affecting diagram structure."""
        # Remove markdown code block markers if present, preserving content structure
        if "```" in code:
            lines = []
            in_block = False
            for line in code.split("\n"):
                if line.strip().startswith("```"):
                    in_block = not in_block
                    continue
                if in_block:
                    lines.append(line)  # Keep the line exactly as is inside code block
            if lines:
                code = "\n".join(lines)
            
        # Process remaining lines for comments while preserving structure
        processed_lines = []
        for line in code.split("\n"):
            # Skip full-line comments for Mermaid
            if line.strip().startswith("%"):
                continue
                
            # Remove inline comments without affecting indentation
            if "%" in line:
                line = line[:line.index("%")]
                
            # Keep the line, preserving its exact indentation
            processed_lines.append(line.rstrip())  # Only remove trailing whitespace
            
        # Join lines back together preserving exact structure
        code = "\n".join(processed_lines)
        
        # Remove any remaining backticks without affecting structure
        code = code.replace("`", "")
        
        # Remove leading/trailing blank lines but preserve internal whitespace
        return code.strip("\n")
        
    def _validate_mermaid(self, code: str) -> ValidationResult:
        """Validate Mermaid diagram syntax."""
        return DiagramValidator.validate(code, DiagramType.MERMAID)
        
    def _validate_plantuml(self, code: str) -> ValidationResult:
        """Validate PlantUML diagram syntax."""
        return DiagramValidator.validate(code, DiagramType.PLANTUML)

    def _get_syntax_rules(self, syntax_type: str) -> str:
        """Get syntax-specific rules based on the diagram type."""
        if (syntax_type.lower() == 'mermaid'):
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
            'gantt': ['gantt', 'timeline', 'schedule', 'project plan', 'time', 'project timeline', 'task schedule', 'task timeline'],
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

        # Build example section if example exists
        example_section = ""
        if example_code:
            example_section = f"""
Example of a valid {specific_type} diagram in {syntax_type}:
{example_code}

Additional rule: Follow the structure shown in the example above.
"""

        # Format context section appropriately
        formatted_context = ""
        if context_section:
            formatted_context = context_section
            
            # Log that we're using RAG context
            log_info(f"Using RAG context of {len(formatted_context)} characters for diagram generation")
        else:
            # If no context available, adjust prompt to work without it
            log_info("No RAG context available, generating diagram based on description only")
            formatted_context = "No code context provided. Create diagram based on description only."

        prompt = self.PROMPT_TEMPLATES["generate"].format(
            description=description,
            diagram_type=specific_type,
            syntax_type=syntax_type,
            context_section=formatted_context,
            example_section=example_section,
            syntax_rules=syntax_rules
        )

        model = agent_config.model_name if agent_config and agent_config.enabled else self.default_model
        temperature = agent_config.temperature if agent_config and agent_config.enabled else 0.2
        
        # Use a special system prompt that emphasizes using the code context
        context_system_prompt = """You are a diagram generation expert. Your task is to:
1. CAREFULLY ANALYZE the provided code context
2. CREATE an accurate diagram that represents the code structure and relationships
3. Include ALL important components from the provided context
4. Return ONLY the diagram code with no additional text or explanation

The code context contains the actual implementation that your diagram should accurately represent."""

        system = context_system_prompt if context_section else (
            agent_config.system_prompt if agent_config and agent_config.enabled else None
        )

        try:
            log_llm("Starting LLM generation", {
                "model": model,
                "prompt_length": len(prompt),
                "context_length": len(formatted_context),
                "temperature": temperature,
                "has_system_prompt": system is not None
            })
            
            # TODO: If context is very large, consider chunking it or using a different approach
            
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
                # Extract all code blocks, preserving exact indentation and diagram type
                code_blocks = []
                lines = raw_content.split('\n')
                in_block = False
                current_block = []
                
                for line in lines:
                    if line.startswith("```"):
                        if in_block:
                            # End of block
                            code_blocks.append('\n'.join(current_block))
                            current_block = []
                            in_block = False
                        else:
                            # Start of block - skip the ``` line itself
                            in_block = True
                    elif in_block:
                        # Inside a block - keep the line exactly as is
                        current_block.append(line)
                        
                if code_blocks:
                    # Take the first code block that was found
                    # Don't strip() to preserve exact indentation
                    return code_blocks[0]
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
    ) -> DiagramAgentOutput:
        """Generate a diagram with validation and fixing."""
        if not options:
            options = DiagramGenerationOptions()

        log_info(f"Generating {diagram_type} diagram for: {description}")

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

        return output

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
        requirements = await self._determine_requirements(
            state.description,
            state.diagram_type,
            rag_directory=rag_directory
        )
        state.requirements = requirements
        state.rag_provider = requirements.get("rag_provider")
        state.context_section = requirements.get("rag_context", "")
        
        if state.context_section:
            state.notes.append(f"Found relevant code context ({len(state.context_section)} characters)")

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
            state.code = self._strip_comments(raw_code).strip("\n")

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
                state.code = self._strip_comments(state.code).strip("\n")

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
            elif '@startgantt' in first_line or 'project' in code.lower():
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
        system_prompt = f"""Reference Example ({specific_type} diagram):

{example_code}

CRITICAL RULES:
1. Keep EXACTLY the same diagram type ({specific_type})
2. Preserve the exact indentation and structure as in the original code
3. Only fix the syntax errors identified in validation
4. Never convert between different diagram types (e.g. mindmap to flowchart)
5. Keep the same nodes and relationships, just fix their syntax

Your output must match:
- Same diagram type as original ({specific_type})
- Same indentation style
- Same structure and organization
- Only syntax errors fixed
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
