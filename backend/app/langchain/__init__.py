"""
KavachAI — LangChain Adapter Package
Provides local sovereign LLM adapters, system prompts, and tool interfaces.
Owned by: Person 2
"""

# LangChain adapter package for KavachAI
from app.langchain.model_adapter import (
    KavachLLM,
    get_reasoning_llm,
    get_coding_llm,
)

__all__ = ["KavachLLM", "get_reasoning_llm", "get_coding_llm"]
