"""Core diagram generation and validation logic."""

import os
from typing import Any, Dict, List, Optional, Tuple, Union

from diagram_generator.backend.agents import DiagramAgent
from diagram_generator.backend.models.configs import DiagramGenerationOptions, DiagramRAGConfig
from diagram_generator.backend.services.ollama import OllamaService
from diagram_generator.backend.utils.rag import RAGProvider

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
{{
    "valid": boolean,
    "errors": string[],
    "suggestions": string[]
}}

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
    ) -> Tuple[str, List[str]]:
        """Generate a diagram from a description.
        
        Args:
            description: Text description of desired diagram
            diagram_type: Target diagram syntax type
            options: Optional generation parameters
        
        Returns:
            Tuple of (diagram code, list of notes/warnings)
        """
        # Convert dict options to DiagramGenerationOptions if needed
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
                self._setup_rag_provider(generation_options.rag)
                
            # Generate diagram with agent
            return await self.diagram_agent.generate_diagram(
                description=description,
                diagram_type=diagram_type,
                options=generation_options,
                rag_provider=self.rag_provider
            )
            
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

        # Try to extract diagram code from markdown blocks
        if "```mermaid" in raw_response:
            try:
                code = raw_response.split("```mermaid")[1].split("```")[0].strip()
            except IndexError:
                notes.append("Failed to extract diagram code from markdown")
        
        try:
            # Validate the generated diagram
            validation = await self.validate_diagram(code, diagram_type)
            if isinstance(validation, dict) and not validation.get("valid", False):
                notes.extend(validation.get("errors", []))
        except Exception as e:
            notes.append(f"Validation warning: {str(e)}")
        
        return code, notes

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
        from diagram_generator.backend.utils.diagram_validator import DiagramValidator, DiagramType
        
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
        
    def _setup_rag_provider(self, rag_config: DiagramRAGConfig) -> None:
        """Set up the RAG provider with configuration.
        
        Args:
            rag_config: RAG configuration
        """
        # Only set up if there's a valid directory
        if not rag_config.api_doc_dir or not os.path.isdir(rag_config.api_doc_dir):
            return
            
        # Initialize RAG provider and load documents
        self.rag_provider = RAGProvider(
            config=rag_config,
            ollama_base_url=self.llm_service.base_url
        )
        self.rag_provider.load_docs_from_directory()
