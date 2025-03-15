"""Service for generating diagrams from descriptions."""

from typing import Dict, List, Optional, Tuple
import logging
from diagram_generator.backend.core.diagram_generator import DiagramGenerator
from diagram_generator.backend.utils.diagram_validator import DiagramType
from diagram_generator.backend.models.configs import DiagramGenerationOptions
from diagram_generator.backend.api.logs import log_info, log_error

logger = logging.getLogger(__name__)

class DiagramGeneratorService:
    """Service for generating diagrams from descriptions."""

    def __init__(self, diagram_agent, storage_service):
        self.diagram_agent = diagram_agent
        self.storage_service = storage_service

    async def generate_diagram(self, request) -> Dict:
        """Generate a diagram from the given request."""
        try:
            # Convert type to proper enum
            diagram_type = DiagramType.from_string(request.syntax_type)
            if not diagram_type:
                raise ValueError(f"Unsupported diagram type: {request.syntax_type}")

            # Prepare generation options
            options = DiagramGenerationOptions()
            if request.options:
                options = DiagramGenerationOptions.parse_obj(request.options)
                if request.model:
                    options.agent.model_name = request.model

            # Generate the diagram
            code, notes = await self.diagram_agent.generate_diagram(
                description=request.description,
                diagram_type=diagram_type.value,
                options=options
            )

            # Validate and clean the generated code
            validation = await self.diagram_agent.validate_diagram(
                code=code,
                diagram_type=diagram_type.value
            )

            return {
                "code": code,
                "type": diagram_type.value,
                "subtype": request.subtype or "auto",
                "notes": notes,
                "validation": validation
            }

        except Exception as e:
            log_error(f"Failed to generate diagram: {str(e)}", exc_info=True)
            raise