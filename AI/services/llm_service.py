"""
LLM Service - wraps ChatGroq for use by the agentic executor.
"""
from AI.config import LLMConfig
from langchain_groq import ChatGroq


class LLMService:
    """
    Thin wrapper around ChatGroq.
    Kept for backward compatibility; new code uses get_llm() directly.
    """

    def __init__(self, api_key: str, config: LLMConfig):
        self.config = config
        self._llm = ChatGroq(
            api_key=api_key,
            model=config.model_name,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
        )

    def get_llm(self) -> ChatGroq:
        """Return the underlying ChatGroq instance."""
        return self._llm

    def invoke(self, input_text: str, **kwargs):
        """Invoke the LLM with a plain string prompt."""
        from langchain_core.messages import HumanMessage
        return self._llm.invoke([HumanMessage(content=input_text)], **kwargs)

    def generate_response(self, prompt: str, **kwargs) -> str:
        """Generate a plain text response."""
        response = self.invoke(prompt, **kwargs)
        return response.content
