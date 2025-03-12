"""Service for generating diagrams from textual descriptions."""

import logging
from typing import Optional

from ..backend.utils.diagram_validator import DiagramValidator, DiagramType
from ..backend.utils.retry import retry_with_backoff
from ..models.diagrams import DiagramRequest, DiagramResponse

logger = logging.getLogger(__name__)

class DiagramGeneratorService:
    """Service for generating diagrams from descriptions."""

    def __init__(self, diagram_agent, storage_service):
        self.diagram_agent = diagram_agent
        self.storage_service = storage_service

    @retry_with_backoff(max_attempts=3)
    async def generate_diagram(self, request: DiagramRequest) -> DiagramResponse:
        """Generate a diagram from the given request."""
        try:
            # Generate diagram code
            diagram_code = await self.diagram_agent.generate_diagram_code(
                request.description,
                request.diagram_type.lower() if request.diagram_type else None
            )

            # Detect or validate diagram type
            detected_type = DiagramValidator.detect_type(diagram_code)
            if not detected_type and request.diagram_type:
                detected_type = DiagramType.from_string(request.diagram_type)
            
            if not detected_type:
                raise ValueError("Unable to determine diagram type")

            # Validate the generated code
            validation_result = DiagramValidator.validate(diagram_code, detected_type)
            if not validation_result.is_valid:
                logger.error(f"Generated diagram validation failed: {validation_result.errors}")
                # Attempt to fix common issues
                diagram_code = await self.diagram_agent.fix_diagram_code(
                    diagram_code,
                    validation_result.errors,
                    detected_type.value
                )
                # Revalidate after fixes
                validation_result = DiagramValidator.validate(diagram_code, detected_type)
                if not validation_result.is_valid:
                    raise ValueError(f"Invalid diagram code: {validation_result.errors}")

            # Store the generated diagram
            diagram_id = await self.storage_service.store_diagram(
                code=diagram_code,
                diagram_type=detected_type.value,
                description=request.description
            )

            return DiagramResponse(
                diagram_id=diagram_id,
                code=diagram_code,
                diagram_type=detected_type.value
            )

        except Exception as e:
            logger.error(f"Error generating diagram: {str(e)}")
            raise