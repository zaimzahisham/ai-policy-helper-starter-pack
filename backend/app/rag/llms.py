"""LLM provider implementations."""
import logging
from typing import List, Dict
from openai import OpenAI

logger = logging.getLogger(__name__)


def _build_messages(
    query: str,
    contexts: List[Dict],
    system_prompt_base: str,
    agent_guide: str | None = None,
    required_output_format: str | None = None,
) -> List[Dict[str, str]]:
    """
    Build messages array for LLM generation.
    
    Shared helper function used by OpenAILLM and OllamaLLM to construct
    messages with consistent formatting.
    
    Args:
        query: User question
        contexts: Retrieved context chunks
        system_prompt_base: Base system prompt for the assistant role
        agent_guide: Internal SOP guide (optional)
        required_output_format: Required output format specification (optional)
    
    Returns:
        List of message dictionaries with "role" and "content" keys
    """
    # System instructions: base behavior + internal SOP + required output format
    system_prompt = system_prompt_base
    if agent_guide:
        system_prompt += "\n\nInternal SOP for agents:\n" + agent_guide
    if required_output_format:
        system_prompt += "\n\n" + required_output_format

    # Build user-visible part of the prompt: question + sources
    sources_block = f"Question: {query}\nSources:\n"
    for c in contexts:
        sources_block += f"- {c.get('title')} | {c.get('section')}\n{c.get('text')[:600]}\n---\n"
    sources_block += "Write a concise, accurate answer grounded in the sources. If unsure, say so."

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": sources_block},
    ]


class StubLLM:
    """
    Deterministic stub LLM for offline testing.
    
    Produces structured output matching the required format contract.
    Used when no API key is provided or as fallback.
    """
    
    def __init__(self, agent_guide: str | None = None, required_output_format: str | None = None):
        # We accept agent_guide and required_output_format for API symmetry with OpenAILLM,
        # but keep StubLLM output simple and deterministic.
        self.agent_guide = agent_guide or ""
        self.required_output_format = required_output_format or ""

    def generate(self, query: str, contexts: List[Dict]) -> str:
        """
        Generate stub answer with structured format.
        
        Stub output is formatted to match the contract we expect from real LLMs:
        - Answer: short direct answer
        - Sources: bullet list of Title — Section
        - Details: longer supporting text (truncated)
        
        Args:
            query: User question
            contexts: Retrieved context chunks
        
        Returns:
            Formatted answer string
        """
        # Naive "answer" that just acknowledges the sources
        answer_line = "Based on the policy documents below, here is a summary answer"

        # Build sources list
        source_lines = []
        for c in contexts:
            sec = c.get("section") or "Section"
            source_lines.append(f"- {c.get('title')} — {sec}")

        # Naive summary of top contexts for Details section
        joined = " ".join([c.get("text", "") for c in contexts])
        details = joined[:600] + ("..." if len(joined) > 600 else "")

        lines = [
            "Answer (stub):",
            answer_line,
            "",
            "Sources:",
            *source_lines,
            "",
            "Details:",
            details,
        ]
        return "\n".join(lines)


class OpenAILLM:
    """
    OpenAI LLM provider using GPT-4o-mini.
    
    Uses system/user message split with internal SOP and required output format.
    """
    
    def __init__(self, api_key: str, system_prompt_base: str | None = None, agent_guide: str | None = None, required_output_format: str | None = None):
        self.client = OpenAI(api_key=api_key)
        self.system_prompt_base = system_prompt_base or ""
        self.agent_guide = agent_guide or ""
        self.required_output_format = required_output_format or ""

    def generate(self, query: str, contexts: List[Dict]) -> str:
        """
        Generate answer using OpenAI API.
        
        System prompt includes base role, internal SOP, and required output format.
        User prompt contains question and retrieved context.
        
        Args:
            query: User question
            contexts: Retrieved context chunks
        
        Returns:
            Generated answer string
        """
        # Build messages using shared helper
        messages = _build_messages(
            query=query,
            contexts=contexts,
            system_prompt_base=self.system_prompt_base,
            agent_guide=self.agent_guide,
            required_output_format=self.required_output_format,
        )

        try:
            logger.debug(f"Calling OpenAI API (model: gpt-4o-mini, context_chunks: {len(contexts)})")
            resp = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=0.1
            )
            answer = resp.choices[0].message.content
            logger.debug(f"OpenAI API call successful (response length: {len(answer)} chars)")
            return answer
        except Exception as e:
            logger.error(f"OpenAI API call failed: {str(e)}", exc_info=True)
            raise


class OllamaLLM:
    """
    Ollama LLM provider for local model inference.
    
    Uses Ollama's OpenAI-compatible API endpoint to generate responses with local models.
    Supports system/user message split with internal SOP and required output format.
    """
    
    def __init__(self, host: str, model: str, system_prompt_base: str | None = None, agent_guide: str | None = None, required_output_format: str | None = None):
        """
        Initialize Ollama LLM provider.
        
        Args:
            host: Ollama server URL (e.g., "http://ollama:11434")
            model: Model name to use (e.g., "qwen2.5:0.5b", "llama3.2", "mistral", "llama2")
            system_prompt_base: Base system prompt for the assistant role
            agent_guide: Internal SOP guide for agent behavior
            required_output_format: Required output format specification
        """
        # Ollama provides OpenAI-compatible API at /v1 endpoint
        base_url = f"{host.rstrip('/')}/v1"
        # API key is required by OpenAI client but not used by Ollama
        self.client = OpenAI(base_url=base_url, api_key="ollama")
        self.model = model
        self.system_prompt_base = system_prompt_base or ""
        self.agent_guide = agent_guide or ""
        self.required_output_format = required_output_format or ""

    def generate(self, query: str, contexts: List[Dict]) -> str:
        """
        Generate answer using Ollama's OpenAI-compatible API.
        
        System prompt includes base role, internal SOP, and required output format.
        User prompt contains question and retrieved context.
        
        Args:
            query: User question
            contexts: Retrieved context chunks
        
        Returns:
            Generated answer string
        """
        # Build messages using shared helper
        messages = _build_messages(
            query=query,
            contexts=contexts,
            system_prompt_base=self.system_prompt_base,
            agent_guide=self.agent_guide,
            required_output_format=self.required_output_format,
        )

        try:
            logger.debug(f"Calling Ollama API (model: {self.model}, context_chunks: {len(contexts)})")
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.1  # Low temperature for consistent, factual responses
            )
            answer = resp.choices[0].message.content
            logger.debug(f"Ollama API call successful (response length: {len(answer)} chars)")
            return answer
        except Exception as e:
            logger.error(f"Ollama API call failed: {str(e)}", exc_info=True)
            raise
        