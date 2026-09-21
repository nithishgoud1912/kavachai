"""
KavachAI — LangChain Adapter Package
Provides local sovereign LLM adapters, system prompts, and tool interfaces.
"""

# LangChain adapter package for KavachAI
# Contains: model_adapter.py (KavachLLM), prompts.py, tools.py (Person B)
from app.langchain.model_adapter import (
    KavachLLM,
    get_reasoning_llm,
    get_coding_llm,
)

__all__ = ["KavachLLM", "get_reasoning_llm", "get_coding_llm"]
