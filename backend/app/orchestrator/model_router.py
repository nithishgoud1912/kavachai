"""
KavachAI — Model Router (Single Point of Model Dispatch)
Implements: NFR-MNT-2 (swap models without touching agent logic),
            NFR-SEC-1 (all inference stays local — enforced here),
            API_Reference.md §9

THIS IS THE ONLY FILE that references the Ollama endpoint/host directly.
No agent may import an Ollama client or httpx to call Ollama — all model
calls MUST go through this router.

route(task_type) -> ModelEndpoint
Supported task_types: "text_reasoning", "classification", "embedding", "vision"
"""

import httpx
import logging
from typing import Optional, List, Dict, Any

from app.config import settings

logger = logging.getLogger(__name__)


def prepare_vision_image(image_bytes: bytes) -> bytes:
    """Bound image token cost on CPU deployments while preserving aspect ratio."""
    import io
    from PIL import Image, ImageOps
    with Image.open(io.BytesIO(image_bytes)) as source:
        if source.width * source.height > 40000000:
            raise ValueError('Vision image exceeds the 40 megapixel processing limit')
        image = ImageOps.exif_transpose(source)
        image.thumbnail((settings.VISION_MAX_IMAGE_EDGE, settings.VISION_MAX_IMAGE_EDGE), Image.Resampling.LANCZOS)
        if image.mode in ('RGBA', 'LA') or 'transparency' in image.info:
            rgba = image.convert('RGBA')
            background = Image.new('RGBA', rgba.size, 'white')
            background.alpha_composite(rgba)
            image = background.convert('RGB')
        else:
            image = image.convert('RGB')
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        return buffer.getvalue()


class ModelRouter:
    """
    Sole point of model dispatch. All agents call through here.

    This is where:
    - NFR-SEC-1 is enforced (only local endpoints)
    - NFR-MNT-2 is satisfied (swap model by changing config, not agent code)
    - Model selection per task type is centralized
    """

    def __init__(self):
        from urllib.parse import urlparse
        host = urlparse(settings.OLLAMA_HOST)
        if host.scheme not in ("http", "https") or host.hostname not in settings.ALLOWED_INFERENCE_HOSTS.split(",") or host.username or host.password:
            raise ValueError("Inference endpoint must be in ALLOWED_INFERENCE_HOSTS")
        self._base_url = settings.OLLAMA_HOST
        self._client: httpx.AsyncClient = httpx.AsyncClient(
            base_url=self._base_url,
            trust_env=False,
            timeout=httpx.Timeout(settings.LLM_TIMEOUT_SECONDS, connect=5.0),
        )
        self._ollama_online: Optional[bool] = None
        self._last_ping: float = 0.0
        # Task type -> model name mapping (NFR-MNT-2: change here only)
        self._model_map = {
            "text_reasoning": settings.LLM_MODEL,   # Qwen 2.5 3B — synthesis, planning, verification
            "classification": settings.LLM_MODEL,    # Same model for classification (scope check)
            "embedding": settings.EMBEDDING_MODEL,    # nomic-embed-text
            "vision": settings.VISION_MODEL,         # Qwen 2.5-VL — visual P&ID & photo reasoning
            "coding": settings.CODING_MODEL,            # Qwen 2.5 3B — coding / tool invocation
        }

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self._base_url,
                trust_env=False,
                timeout=httpx.Timeout(settings.LLM_TIMEOUT_SECONDS, connect=5.0),
            )
        return self._client

    async def is_ollama_available(self) -> bool:
        """Quick check if Ollama server is reachable."""
        import time
        now = time.time()
        if self._ollama_online is True and (now - self._last_ping) < 5.0:
            return True

        self._last_ping = now
        try:
            resp = await self.client.get("/api/tags", timeout=5.0)
            self._ollama_online = (resp.status_code == 200)
        except Exception as e:
            logger.warning("Ollama ping check failed: %s: %s", type(e).__name__, e)
            self._ollama_online = False
            self._last_ping = 0.0
        return self._ollama_online


    def get_model(self, task_type: str) -> Optional[str]:
        """
        Resolve which model handles a given task type.
        Implements: API_Reference.md §9 route(task_type) -> ModelEndpoint
        """
        model = self._model_map.get(task_type)
        if model is None:
            raise ValueError(f"Unknown task_type: {task_type}")
        return model

    async def generate(
        self,
        prompt: str,
        task_type: str = "text_reasoning",
        system: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 2048,
        format: Optional[str] = None,
    ) -> str:
        """
        Generate text via the local LLM.
        This is the ONLY way agents should call the LLM.

        Args:
            prompt: the user/task prompt
            task_type: determines which model to use
            system: optional system prompt
            temperature: sampling temperature (low for factual tasks)
            max_tokens: max response length
            format: optional response format ("json" for structured output)

        Returns:
            The generated text response

        Raises:
            RuntimeError if the model call fails
        """
        model = self.get_model(task_type)
        if model is None:
            raise RuntimeError(f"No model configured for task_type: {task_type}")

        if not await self.is_ollama_available():
            return self._offline_generate(prompt, task_type, format)

        payload: Dict[str, Any] = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
                "num_ctx": settings.LLM_CONTEXT_TOKENS,
            },
        }

        if system:
            payload["system"] = system

        if format:
            payload["format"] = format

        try:
            resp = await self.client.post("/api/generate", json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data.get("response", "")
        except Exception as e:
            logger.error("Ollama generate call failed: %s: %s", type(e).__name__, e)
            return self._offline_generate(prompt, task_type, format, error=e)

    async def generate_chat(
        self,
        messages: List[Dict[str, str]],
        task_type: str = "text_reasoning",
        temperature: float = 0.1,
        max_tokens: int = 2048,
        format: Optional[str] = None,
    ) -> str:
        """
        Chat-style generation for multi-turn prompts.

        Args:
            messages: list of {"role": "system"|"user"|"assistant", "content": "..."}
            task_type: determines which model to use
        """
        model = self.get_model(task_type)
        if model is None:
            raise RuntimeError(f"No model configured for task_type: {task_type}")

        if not await self.is_ollama_available():
            last_msg = messages[-1]["content"] if messages else ""
            return self._offline_generate(last_msg, task_type, format)

        payload: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
                "num_ctx": settings.LLM_CONTEXT_TOKENS,
            },
        }

        if format:
            payload["format"] = format

        try:
            resp = await self.client.post("/api/chat", json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data.get("message", {}).get("content", "")
        except Exception as e:
            logger.error("Ollama chat call failed: %s: %s", type(e).__name__, e)
            last_msg = messages[-1]["content"] if messages else ""
            return self._offline_generate(last_msg, task_type, format, error=e)

    async def generate_chat_with_tools(
        self,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
        task_type: str = "text_reasoning",
        temperature: float = 0.1,
        max_tokens: int = 2048,
    ) -> Dict[str, Any]:
        """
        Chat generation with native Ollama tool-calling.

        Separate from generate_chat() to preserve backward compatibility.
        Only KavachLLM adapter calls this method for LangChain tool workflows.

        Args:
            messages: conversation messages (may include tool role with tool_name)
            tools: list of tool schemas in Ollama function-calling format
            task_type: determines which model to use
            temperature: sampling temperature
            max_tokens: max response length

        Returns:
            {"content": str, "tool_calls": Optional[List[Dict]]}
        """
        model = self.get_model(task_type)
        if model is None:
            raise RuntimeError(f"No model configured for task_type: {task_type}")

        if not await self.is_ollama_available():
            # Fallback: return text-only response without tool_calls
            last_msg = messages[-1].get("content", "") if messages else ""
            return {
                "content": self._offline_generate(last_msg, task_type, None),
                "tool_calls": None,
            }

        payload: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": temperature, "num_predict": max_tokens},
            "tools": tools,
        }

        try:
            resp = await self.client.post("/api/chat", json=payload)
            resp.raise_for_status()
            data = resp.json()
            msg = data.get("message", {})
            return {
                "content": msg.get("content", ""),
                "tool_calls": msg.get("tool_calls"),
            }
        except Exception:
            last_msg = messages[-1].get("content", "") if messages else ""
            return {
                "content": self._offline_generate(last_msg, task_type, None),
                "tool_calls": None,
            }

    async def generate_vision(
        self,
        prompt: str,
        image_bytes: bytes,
        system: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 1024,
        format: Optional[str] = "json",
    ) -> str:
        """
        Multimodal visual generation using Qwen2.5-VL through local Ollama.
        Encodes the image bytes to base64 and sends via Ollama /api/chat.
        """
        import base64
        model = self.get_model("vision")
        if model is None:
            raise RuntimeError("No model configured for task_type: vision")

        if not await self.is_ollama_available():
            return self._offline_generate(prompt, "vision", format)

        import asyncio
        prepared_image = await asyncio.to_thread(prepare_vision_image, image_bytes)
        b64_img = base64.b64encode(prepared_image).decode("utf-8")
        payload: Dict[str, Any] = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                    "images": [b64_img],
                }
            ],
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        if system:
            payload["messages"].insert(0, {"role": "system", "content": system})

        if format:
            payload["format"] = format

        try:
            resp = await self.client.post(
                "/api/chat",
                json=payload,
                timeout=httpx.Timeout(settings.VISION_TIMEOUT_SECONDS, connect=2.0),
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("message", {}).get("content", "")
        except Exception:
            return self._offline_generate(prompt, "vision", format)


    async def embed(
        self,
        texts: List[str],
    ) -> List[List[float]]:
        """
        Generate embeddings for a list of texts.
        Uses the embedding model (nomic-embed-text).

        Args:
            texts: list of text strings to embed

        Returns:
            List of embedding vectors (each 768-dim for nomic-embed-text)
        """
        model = self.get_model("embedding")

        if not await self.is_ollama_available():
            raise RuntimeError("Local embedding model unavailable; ingestion aborted")

        try:
            resp = await self.client.post(
                "/api/embed",
                json={"model": model, "input": texts},
                timeout=30.0,
            )
            resp.raise_for_status()
            data = resp.json()
            embeddings = data.get("embeddings", [])
            if embeddings and len(embeddings) == len(texts) and all(len(v) == settings.EMBEDDING_DIMENSION for v in embeddings):
                return embeddings
        except Exception:
            pass

        raise RuntimeError("Embedding request failed; no synthetic vectors stored")


    def _offline_generate(self, prompt, task_type, fmt, error: Optional[Exception] = None):
        err_msg = f": {type(error).__name__}: {error}" if error else ""
        raise RuntimeError(f"Local inference failed for {task_type}{err_msg}; no fallback evidence is generated")

    async def close(self):
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()


# Singleton instance
model_router = ModelRouter()
