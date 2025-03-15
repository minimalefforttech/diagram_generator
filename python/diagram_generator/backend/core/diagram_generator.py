"""Core diagram generation and validation logic."""

import os
import uuid
from typing import Any, Dict, List, Optional, Tuple, Union

from diagram_generator.backend.agents import DiagramAgent, DiagramAgentOutput
from diagram_generator.backend.models.configs import DiagramGenerationOptions, DiagramRAGConfig
from diagram_generator.backend.services.ollama import OllamaService
from diagram_generator.backend.utils.rag import RAGProvider
from diagram_generator.backend.utils.diagram_validator import DiagramValidator, DiagramType
from diagram_generator.backend.api.logs import log_info, log_error

class DiagramGenerator:
    """Handles generation and validation of diagrams."""

    def __init__(self, llm_service: OllamaService):
        """Initialize DiagramGenerator.
        
        Args:
            llm_service: LLM service for diagram generation
        """
        self.llm_service = llm_service
        self.diagram_agent = DiagramAgent(
            base_url=self.llm_service.base_url,
            default_model=self.llm_service.model
        )
        self.rag_provider = None
        
        # System prompts for different operations
        self.prompts = {
            "generate": """You are a diagram expert. Convert the following description into 
a valid diagram using {type} syntax. Respond ONLY with the diagram code without explanations or markdown:

Description: {description}
""",
            "validate": """You are a {type} syntax validator. Check if the following diagram 
code is valid and return a JSON response with format:
{
    "valid": boolean,
    "errors": string[],
    "suggestions": string[]
}

Code to validate:
{code}
""",
            "convert": """You are a diagram conversion expert. Convert the following {source_type} 
diagram into a valid {target_type} diagram while preserving the semantics:

Source diagram:
{diagram}
"""
        }

    async def generate_diagram(
        self,
        description: str,
        diagram_type: str = "mermaid", 
        options: Optional[Union[Dict, DiagramGenerationOptions]] = None
    ) -> DiagramAgentOutput:
        """Generate a diagram from a description."""
        # Convert dict options to DiagramGenerationOptions
        generation_options = self._prepare_options(options)
        
        # Extract model from options if provided
        model = None
        if isinstance(options, dict):
            model = options.get("model")
            if model and isinstance(generation_options, DiagramGenerationOptions):
                generation_options.agent.model_name = model
        
        # Use the agent-based approach if enabled
        if generation_options.agent.enabled:
            # Initialize RAG provider if needed
            if generation_options.rag.enabled and not self.rag_provider:
                await self._setup_rag_provider(generation_options.rag)
                
            # Generate diagram with agent
            return await self.diagram_agent.generate_diagram(
                description=description,
                diagram_type=diagram_type,
                options=generation_options,
                rag_provider=self.rag_provider
            )
        else:
            # Fall back to legacy implementation if agent is disabled
            prompt = self.prompts["generate"].format(
                type=diagram_type,
                description=description
            )
            
            response = self.llm_service.generate_completion(
                prompt=prompt,
                temperature=0.2,
                model=model or self.llm_service.model
            )
            
            # Extract diagram code and any warnings
            raw_response = response["response"]
            code = raw_response
            notes = []

            # Try to extract diagram code from markdown blocks based on type
            if diagram_type.lower() == "mermaid" and "```mermaid" in raw_response:
                try:
                    code = raw_response.split("```mermaid")[1].split("```")[0].strip()
                except IndexError:
                    notes.append("Failed to extract Mermaid diagram code from markdown")
            elif diagram_type.lower() == "plantuml" and "```plantuml" in raw_response:
                try:
                    code = raw_response.split("```plantuml")[1].split("```")[0].strip()
                except IndexError:
                    notes.append("Failed to extract PlantUML diagram code from markdown")

            # Clean and validate the generated code for specific diagram types
            if diagram_type.lower() == "mermaid":
                code = DiagramValidator._clean_mermaid_code(code)
            elif diagram_type.lower() == "plantuml":
                code = DiagramValidator._clean_plantuml_code(code)
            
            try:
                # Validate the generated diagram
                validation = await self.validate_diagram(code, diagram_type)
                valid = validation.get("valid", False) if isinstance(validation, dict) else False
                if not valid:
                    notes.extend(validation.get("errors", []) if isinstance(validation, dict) else [])
            except Exception as e:
                notes.append(f"Validation warning: {str(e)}")
                valid = False

            # Create DiagramAgentOutput for legacy path
            return DiagramAgentOutput(
                code=code,
                diagram_type=diagram_type,
                notes=notes,
                valid=valid,
                iterations=1,
                diagram_id=str(uuid.uuid4()),
                conversation_id=str(uuid.uuid4())
            )

    async def validate_diagram(
        self,
        code: str,
        diagram_type: str = "mermaid"
    ) -> Dict:
        """Validate diagram syntax.
        
        Args:
            code: Diagram code to validate
            diagram_type: Type of diagram syntax
        
        Returns:
            Dictionary containing validation results
        """
        try:
            # First use our static validator for basic syntax checking
            validation_result = DiagramValidator.validate(code, diagram_type)

            # If the validation fails, return errors
            if not validation_result.valid:
                return validation_result.to_dict()

            # If validation passes, use agent for deeper semantic validation
            try:
                agent_result = await self.diagram_agent.validate_diagram(
                    code=code,
                    diagram_type=diagram_type
                )
                # Merge suggestions from both validations
                if agent_result["valid"]:
                    agent_result["suggestions"] = list(set(
                        validation_result.suggestions + agent_result.get("suggestions", [])
                    ))
                return agent_result
            except Exception:
                # Fall back to basic validation result if agent fails
                return validation_result.to_dict()
        except Exception as e:
            return {
                "valid": False,
                "errors": [str(e)],
                "suggestions": ["Check diagram syntax and type"]
            }

    async def convert_diagram(
        self,
        diagram: str,
        source_type: str,
        target_type: str,
        options = None
    ) -> Tuple[str, List[str]]:
        """Convert diagram between different syntax types.
        
        Args:
            diagram: Source diagram code
            source_type: Source diagram syntax type
            target_type: Target diagram syntax type
        
        Returns:
            Tuple of (converted diagram code, list of notes/warnings)
        """
        prompt = self.prompts["convert"].format(
            source_type=source_type,
            target_type=target_type,
            diagram=diagram
        )
        
        response = self.llm_service.generate_completion(
            prompt=prompt,
            temperature=0.3,
            model=options.get("model") if options else self.llm_service.model
        )
        
        code = response["response"]
        notes = []
        
        try:
            # Validate the converted diagram using the agent
            validation = await self.diagram_agent.validate_diagram(
                code=code,
                diagram_type=target_type
            )
            
            if not validation.get("valid", False):
                notes.extend(validation.get("errors", []))
        except Exception as e:
            notes.append(f"Validation warning: {str(e)}")
            
        return code, notes
        
    async def update_diagram(
        self,
        diagram_code: str,
        update_notes: str,
        diagram_type: str = "mermaid",
        options: Optional[Union[Dict, DiagramGenerationOptions]] = None
    ) -> DiagramAgentOutput:
        """Update an existing diagram based on provided notes/changes.
        
        Args:
            diagram_code: The existing diagram code
            update_notes: Notes/changes to apply to the diagram
            diagram_type: Type of diagram (mermaid, plantuml)
            options: Optional generation options
            
        Returns:
            DiagramAgentOutput containing the updated diagram
        """
        # Convert dict options to DiagramGenerationOptions
        generation_options = self._prepare_options(options)
        
        # Initialize RAG provider if needed
        if generation_options.rag.enabled and not self.rag_provider:
            await self._setup_rag_provider(generation_options.rag)
            
        # Forward the update request to the diagram agent
        return await self.diagram_agent.update_diagram(
            diagram_code=diagram_code,
            update_notes=update_notes,
            diagram_type=diagram_type,
            options=generation_options,
            rag_provider=self.rag_provider
        )
        
    def _prepare_options(
        self, 
        options: Optional[Union[Dict, DiagramGenerationOptions]] = None
    ) -> DiagramGenerationOptions:
        """Prepare and normalize generation options.
        
        Args:
            options: Raw options (dict or object)
            
        Returns:
            DiagramGenerationOptions object
        """
        if options is None:
            return DiagramGenerationOptions()
            
        if isinstance(options, DiagramGenerationOptions):
            return options
            
        # Convert dict to DiagramGenerationOptions
        result = DiagramGenerationOptions()
        
        # Update with provided options
        if isinstance(options, dict):
            # Handle agent options
            if "agent" in options:
                agent_opts = options["agent"]
                if isinstance(agent_opts, dict):
                    if "enabled" in agent_opts:
                        result.agent.enabled = bool(agent_opts["enabled"])
                    if "max_iterations" in agent_opts:
                        result.agent.max_iterations = int(agent_opts["max_iterations"])
                    if "temperature" in agent_opts:
                        result.agent.temperature = float(agent_opts["temperature"])
                    if "model_name" in agent_opts:
                        result.agent.model_name = agent_opts["model_name"]
                    if "system_prompt" in agent_opts:
                        result.agent.system_prompt = agent_opts["system_prompt"]
            
            # Handle RAG options
            if "rag" in options:
                rag_opts = options["rag"]
                if isinstance(rag_opts, dict):
                    if "enabled" in rag_opts:
                        result.rag.enabled = bool(rag_opts["enabled"])
                    if "api_doc_dir" in rag_opts:
                        result.rag.api_doc_dir = rag_opts["api_doc_dir"]
                    if "top_k_results" in rag_opts:
                        result.rag.top_k_results = int(rag_opts["top_k_results"])
                    if "chunk_size" in rag_opts:
                        result.rag.chunk_size = int(rag_opts["chunk_size"])
                    if "chunk_overlap" in rag_opts:
                        result.rag.chunk_overlap = int(rag_opts["chunk_overlap"])
                        
            # Handle custom parameters
            if "custom_params" in options:
                result.custom_params = options["custom_params"]
                
        return result
        
    async def _setup_rag_provider(self, rag_config):
        """Set up RAG provider if enabled."""
        if not rag_config or not rag_config.enabled:
            log_info("RAG disabled, skipping setup")
            self.rag_provider = None
            return
            
        try:
            log_info("Setting up RAG provider")
            self.rag_provider = RAGProvider(
                config=rag_config,
                ollama_base_url=self.llm_service.base_url  # Use base_url from llm_service instead
            )
            
            if not rag_config.api_doc_dir:
                log_info("RAG enabled but no API doc directory provided", 
                         {"warning": "No API doc directory provided"})
                return
                
            # Fix: Pass the directory parameter to load_docs_from_directory
            # Also pass the use_simple_file_splitting parameter to use our improved method
            await self.rag_provider.load_docs_from_directory(
                directory=rag_config.api_doc_dir, 
                use_simple_file_splitting=True
            )
            
            # Log stats after loading
            log_info(f"RAG provider stats", 
                     {"stats": self.rag_provider.stats.model_dump()})
            
        except Exception as e:
            log_error(f"Error setting up RAG provider: {str(e)}", exc_info=True)
            self.rag_provider = None
