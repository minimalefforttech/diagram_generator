"""Diagram agent for generating and refining diagram code."""

import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple

from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage
from langchain_ollama import ChatOllama

from diagram_generator.backend.models.configs import AgentConfig, DiagramGenerationOptions
from diagram_generator.backend.storage.database import Storage, DiagramRecord, ConversationRecord, ConversationMessage
from diagram_generator.backend.utils.caching import DiagramCache
from diagram_generator.backend.utils.rag import RAGProvider
from diagram_generator.backend.utils.retry import RetryConfig, CircuitBreaker, with_retries

class DiagramAgent:
    """Agent responsible for generating and refining diagram code."""

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        default_model: str = "llama3.1:8b",
        cache_dir: str = ".cache/diagrams",
        cache_ttl: Optional[float] = 3600,  # 1 hour default TTL
        storage: Optional[Storage] = None
    ):
        """Initialize DiagramAgent.
        
        Args:
            base_url: Ollama base URL
            default_model: Default LLM model to use
            cache_dir: Directory for caching generated diagrams
            cache_ttl: Time-to-live for cached diagrams in seconds
            storage: Optional storage instance (creates default if None)
        """
        self.base_url = base_url
        self.default_model = default_model
        self.cache_ttl = cache_ttl
        self.cache = DiagramCache(cache_dir=cache_dir)
        self.storage = storage or Storage()
        
        # Configure retry behavior
        self.retry_config = RetryConfig(
            max_attempts=3,
            base_delay=1.0,
            max_delay=5.0,
            exponential_backoff=True,
            exceptions=(Exception,)  # Retry on any exception
        )
        
        # Configure circuit breaker
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            reset_timeout=60.0,
            half_open_timeout=30.0
        )
        
        # Define prompt templates
        self.prompts = {
            "generate": PromptTemplate.from_template(
                """You are a diagram expert. Create a minimal diagram using {diagram_type} syntax.
{context_section}
Keep it extremely simple - use just 2-3 nodes with basic connections.
Follow this exact format:
graph TD;
A-->B;

Description: {description}
"""
            ),
            "validate": PromptTemplate.from_template(
                """You are a {diagram_type} syntax validator. Examine the following diagram code carefully and
return a JSON response with exactly this format:
{{
    "valid": boolean,
    "errors": string[],
    "suggestions": string[]
}}

Code to validate:
{code}

Return only the JSON with no additional text or explanations.
"""
            ),
            "fix": PromptTemplate.from_template(
                """You are a diagram debugging expert specializing in {diagram_type} syntax.
Fix the following {diagram_type} diagram that has these validation errors:
{errors}

Original diagram code:
{code}

Return ONLY the corrected diagram code without explanations or markdown formatting.
Make minimal changes needed to fix the errors.
"""
            )
        }

    def _create_ollama_chat(self, config: AgentConfig = None) -> ChatOllama:
        """Create an Ollama chat model instance."""
        model_name = None
        temperature = 0.1  # Lower temperature for more consistent output
        system = None
        
        if config:
            model_name = config.model_name
            temperature = config.temperature
            system = config.system_prompt
            
        return ChatOllama(
            base_url=self.base_url,
            model=model_name or self.default_model,
            temperature=temperature,
            system=system,
        )

    @with_retries()
    async def _generate_with_llm(
        self,
        description: str,
        diagram_type: str,
        context_section: str,
        agent_config: Optional[AgentConfig]
    ) -> Dict[str, str]:
        """Generate diagram using LLM with retries."""
        chat = self._create_ollama_chat(
            agent_config if agent_config and agent_config.enabled else None
        )
        
        prompt = self.prompts["generate"].format(
            description=description,
            diagram_type=diagram_type,
            context_section=context_section
        )
        
        result = await chat.ainvoke([HumanMessage(content=prompt)])
        
        # Extract content
        if isinstance(result, dict) and "response" in result:
            content = result["response"]
        elif hasattr(result, "content"):
            content = result.content
        else:
            content = str(result)
            
        # Strip formatting and ensure simple output
        content = content.strip()
        if content.startswith("```"):
            lines = content.split("\n")
            content = "\n".join(lines[1:-1] if len(lines) > 2 else lines)
        content = content.replace("```mermaid", "").replace("```", "").strip()
        
        # Normalize graph type
        if content.startswith("graph LR"):
            content = content.replace("graph LR", "graph TD", 1)
            
        # Ensure the content exists
        if not content:
            raise Exception("Empty response from LLM")
            
        return {"content": content}

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
            
        notes = []
            
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
            notes.append("Using cached diagram")
            return cache_entry.value, notes
            
        # Check circuit breaker before generating
        if not self.circuit_breaker.can_execute():
            raise Exception("Circuit breaker is open")

        # Generate diagram with retries
        try:
            result = await self._generate_with_llm(
                description,
                diagram_type,
                context_section,
                options.agent if options.agent.enabled else None
            )
        except Exception as e:
            self.circuit_breaker.record_failure()
            raise  # Re-raise the original exception
            
        # Extract content
        generated_code = result["content"] if isinstance(result, dict) else str(result)
        self.circuit_breaker.record_success()
        
        # Cache successful generation
        self.cache.set(
            description=description,
            diagram_type=diagram_type,
            value=generated_code,
            ttl=self.cache_ttl,
            rag_context=context_section if context_section else None
        )
        
        # Store diagram and conversation
        diagram_id = str(uuid.uuid4())
        conversation_id = str(uuid.uuid4())
        now = datetime.now()
        
        # Store diagram
        diagram_record = DiagramRecord(
            id=diagram_id,
            description=description,
            diagram_type=diagram_type,
            code=generated_code,
            created_at=now,
            tags=set(),
            metadata={
                "agent_enabled": options.agent.enabled if options else False,
                "rag_enabled": options.rag.enabled if options else False,
                "model": options.agent.model_name if options and options.agent.enabled else self.default_model
            }
        )
        self.storage.save_diagram(diagram_record)
        
        # Store conversation
        conversation = ConversationRecord(
            id=conversation_id,
            diagram_id=diagram_id,
            messages=[
                ConversationMessage(
                    role="user",
                    content=description,
                    timestamp=now,
                    metadata={"type": "initial_request"}
                ),
                ConversationMessage(
                    role="assistant",
                    content=generated_code,
                    timestamp=now,
                    metadata={
                        "type": "generation",
                        "diagram_type": diagram_type
                    }
                )
            ],
            created_at=now,
            updated_at=now,
            metadata={
                "rag_context": context_section if context_section else None
            }
        )
        self.storage.save_conversation(conversation)
    
        # Skip validation if agent is disabled
        if not options.agent.enabled:
            return generated_code, notes
            
        # Validate and fix diagram in a loop
        diagram_code = generated_code
        for i in range(options.agent.max_iterations):
            validation = await self.validate_diagram(diagram_code, diagram_type, options.agent)
            
            if validation.get("valid", False):
                if i > 0:
                    notes.append(f"Diagram fixed after {i+1} iterations")
                break
                
            errors = validation.get("errors", [])
            if not errors:
                break
                
            notes.extend(errors)
            
            # Try to fix the diagram
            diagram_code = await self.fix_diagram(
                diagram_code, 
                diagram_type, 
                errors,
                options.agent
            )
            
            # Add note about the current iteration
            notes.append(f"Attempt {i+1}: Applied fixes")
            
            # Update conversation with fixes
            now = datetime.now()
            conversation.messages.append(ConversationMessage(
                role="assistant",
                content=diagram_code,
                timestamp=now,
                metadata={
                    "type": "fix",
                    "iteration": i + 1,
                    "errors": errors
                }
            ))
            conversation.updated_at = now
            self.storage.save_conversation(conversation)
            
        return diagram_code, notes

    async def validate_diagram(
        self,
        code: str,
        diagram_type: str = "mermaid",
        config: Optional[AgentConfig] = None,
    ) -> Dict:
        """Validate diagram syntax."""
        chat = self._create_ollama_chat(config)
        
        prompt = self.prompts["validate"].format(
            diagram_type=diagram_type,
            code=code
        )
        
        result = await chat.ainvoke([HumanMessage(content=prompt)])
        
        try:
            response_text = result["response"] if isinstance(result, dict) and "response" in result else result.content
            return json.loads(response_text)
        except json.JSONDecodeError:
            return {
                "valid": False,
                "errors": ["Failed to parse validation result"],
                "suggestions": []
            }

    async def fix_diagram(
        self,
        code: str,
        diagram_type: str,
        errors: List[str],
        config: Optional[AgentConfig] = None,
    ) -> str:
        """Fix diagram syntax errors."""
        chat = self._create_ollama_chat(config)
        
        prompt = self.prompts["fix"].format(
            diagram_type=diagram_type,
            code=code,
            errors="\n".join(errors)
        )
        
        result = await chat.ainvoke([HumanMessage(content=prompt)])
        if isinstance(result, dict) and "response" in result:
            return result["response"]
        return result.content
