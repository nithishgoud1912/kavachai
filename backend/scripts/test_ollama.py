"""
KavachAI - Ollama Round-Trip Test Script
Phase 0 DoD: confirm Ollama is running and both models respond.

Usage: python scripts/test_ollama.py
"""

import httpx
import sys
import json
import os

# Ensure project root is on the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from app.config import settings


def test_llm():
    """Test that the LLM model responds to a trivial prompt."""
    print(f"Testing LLM: {settings.LLM_MODEL} at {settings.OLLAMA_HOST}...")
    try:
        resp = httpx.post(
            f"{settings.OLLAMA_HOST}/api/generate",
            json={
                "model": settings.LLM_MODEL,
                "prompt": "Respond with exactly: KAVACHAI_OK",
                "stream": False,
            },
            timeout=settings.LLM_TIMEOUT_SECONDS,
        )
        resp.raise_for_status()
        data = resp.json()
        print(f"  [PASS] LLM responded: {data['response'][:100]}")
        return True
    except Exception as e:
        print(f"  [FAIL] LLM failed: {e}")
        return False


def test_embeddings():
    """Test that the embedding model returns a vector of the expected dimension."""
    print(f"Testing embeddings: {settings.EMBEDDING_MODEL} at {settings.OLLAMA_HOST}...")
    try:
        resp = httpx.post(
            f"{settings.OLLAMA_HOST}/api/embed",
            json={
                "model": settings.EMBEDDING_MODEL,
                "input": "Test embedding for KavachAI system.",
            },
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        embeddings = data.get("embeddings", [])
        if embeddings:
            dim = len(embeddings[0])
            expected = settings.EMBEDDING_DIMENSION
            if dim == expected:
                print(f"  [PASS] Embedding dimension: {dim} (matches expected {expected})")
            else:
                print(f"  [WARN] Embedding dimension: {dim} (expected {expected} -- update EMBEDDING_DIMENSION in .env)")
            return True
        else:
            print("  [FAIL] No embeddings returned")
            return False
    except Exception as e:
        print(f"  [FAIL] Embedding failed: {e}")
        return False


def test_ollama_running():
    """Test that Ollama server is reachable."""
    print(f"Testing Ollama connectivity at {settings.OLLAMA_HOST}...")
    try:
        resp = httpx.get(f"{settings.OLLAMA_HOST}/api/tags", timeout=5)
        resp.raise_for_status()
        models = [m["name"] for m in resp.json().get("models", [])]
        print(f"  [PASS] Ollama is running. Available models: {models}")
        return True
    except Exception as e:
        print(f"  [FAIL] Cannot reach Ollama: {type(e).__name__}")
        print(f"         Is Ollama running? Start it with: ollama serve")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("KavachAI -- Ollama Round-Trip Test (Phase 0 DoD)")
    print("=" * 60)

    results = []
    
    # Test connectivity first — skip model tests if Ollama is down
    ollama_ok = test_ollama_running()
    results.append(("Ollama connectivity", ollama_ok))
    
    if ollama_ok:
        results.append(("LLM response", test_llm()))
        results.append(("Embedding response", test_embeddings()))
    else:
        print("\n  Skipping model tests -- Ollama is not reachable.")
        results.append(("LLM response", False))
        results.append(("Embedding response", False))

    print("\n" + "=" * 60)
    print("Results:")
    all_pass = True
    for name, passed in results:
        status = "[PASS]" if passed else "[FAIL]"
        print(f"  {status}: {name}")
        if not passed:
            all_pass = False

    print("=" * 60)
    if all_pass:
        print("Phase 0 Ollama DoD: ALL PASSED")
    else:
        print("Phase 0 Ollama DoD: SOME FAILED -- fix before proceeding")
        sys.exit(1)
