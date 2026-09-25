"""Read-only local readiness check. Never pulls models, packages, or images."""
import asyncio
import json
from pathlib import Path
import shutil
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.config import settings
from app.orchestrator.model_router import model_router


async def command(*args):
    try:
        proc = await asyncio.create_subprocess_exec(*args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        try:
            out, err = await asyncio.wait_for(proc.communicate(), 10)
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            return {"ok": False, "error": "Local command timed out"}
        return {"ok": proc.returncode == 0, "output": out.decode(errors='replace')[:4000], "error": err.decode(errors='replace')[:1000]}
    except OSError as exc:
        return {"ok": False, "error": str(exc)}


async def main():
    checks = {"production_auth": {"ok": settings.ENVIRONMENT == 'production' and not settings.ALLOW_DEMO_SESSIONS}}
    try:
        response = await model_router._client.get('/api/tags')
        response.raise_for_status()
        installed = {m['name']: m.get('digest') for m in response.json().get('models', [])}
        for capability, model in model_router._model_map.items():
            match = model if model in installed else model + ':latest'
            checks[capability] = {"ok": match in installed, "model": model, "digest": installed.get(match)}
        # Exercise the real embedding model to catch wrong dimensions and unavailable weights.
        vectors = await model_router.embed(['Local readiness probe; no confidential content.'])
        checks['embedding_dimensions'] = {"ok": len(vectors) == 1 and len(vectors[0]) == settings.EMBEDDING_DIMENSION}
    except Exception as exc:
        checks['inference'] = {"ok": False, "error": str(exc)[:1000]}
    finally:
        await model_router.close()
    checks['docker'] = await command('docker', 'info', '--format', '{{.ServerVersion}}')
    checks['sandbox_image'] = await command('docker', 'image', 'inspect', settings.SANDBOX_IMAGE, '--format', '{{.Id}}')
    checks['ocr'] = await command(shutil.which('tesseract') or 'tesseract', '--list-langs')
    checks['airgap_evidence'] = {"ok": False, "error": "Requires deployment firewall review and packet capture across host, browser, model service and worker; this script cannot certify it."}
    runtime_ready = all(value['ok'] for key, value in checks.items() if key != 'airgap_evidence')
    print(json.dumps({"runtime_ready": runtime_ready, "airgap_verified": False, "checks": checks}, indent=2))
    return 0 if runtime_ready else 1


if __name__ == '__main__':
    raise SystemExit(asyncio.run(main()))
