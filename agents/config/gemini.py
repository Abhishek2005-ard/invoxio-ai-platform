"""
Invoxio Agent — Gemini LLM Configuration
Initializes the Google Gemini model via LangChain for use in all agent nodes.
"""

from langchain_google_genai import ChatGoogleGenerativeAI
from config.settings import settings


def get_llm(temperature: float = None, streaming: bool = True) -> ChatGoogleGenerativeAI:
    """
    Factory function — returns a configured Gemini LLM instance.

    Args:
        temperature: Override default temperature (0 = deterministic, 1 = creative)
        streaming:   Enable token-by-token streaming (for SSE responses)
    """
    return ChatGoogleGenerativeAI(
        model=settings.gemini_model,
        google_api_key=settings.google_gemini_api_key,
        temperature=temperature if temperature is not None else settings.agent_temperature,
        streaming=streaming,
        max_retries=3,
        convert_system_message_to_human=True,  # Required for Gemini
    )


# Default LLM instances used across the agent graph
llm = get_llm()                        # Streaming (for Act + Reflect nodes)
llm_think = get_llm(streaming=False)   # Non-streaming (for Think/planning node)
