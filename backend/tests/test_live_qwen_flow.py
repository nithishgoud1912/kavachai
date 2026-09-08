"""
Test live query dispatch to Qwen model via model router.
"""
import pytest
import asyncio
from app.orchestrator.model_router import model_router


@pytest.mark.asyncio
async def test_qwen_live_inference():
    """Verify that model_router can communicate with local Ollama if online."""
    online = await model_router.is_ollama_available()
    print(f"\n[Test] Ollama online status: {online}")

    prompt = "Explain in one concise sentence what cavitation in a centrifugal pump is."
    response = await model_router.generate(
        prompt=prompt,
        task_type="text_reasoning",
        max_tokens=60,
    )
    print(f"\n[Test] Model Response:\n{response.strip()}\n")
    assert len(response.strip()) > 10
