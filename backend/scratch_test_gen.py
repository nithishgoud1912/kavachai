import asyncio
import sys
from app.orchestrator.model_router import model_router

async def test():
    try:
        print("Checking Ollama availability...")
        avail = await model_router.is_ollama_available()
        print("Available:", avail)
        print("Calling generate...")
        res = await model_router.generate(
            prompt='Synthesize this: The temperature reached 45C.',
            task_type='text_reasoning',
            format='json',
            max_tokens=100
        )
        print("SUCCESS:", res)
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test())
