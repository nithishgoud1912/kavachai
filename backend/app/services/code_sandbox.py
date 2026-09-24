"""Bounded execution using a preloaded image and an isolated Docker daemon."""
import asyncio
import json
import uuid
from app.config import settings

DEFAULT_TIMEOUT_SECONDS = 30
MEMORY_LIMIT = "256m"
PIDS_LIMIT = 64
MAX_OUTPUT_BYTES = 65536
SANDBOX_IMAGE = settings.SANDBOX_IMAGE


class SandboxResult:
    def __init__(self, stdout, stderr, exit_code, timed_out=False):
        self.stdout, self.stderr, self.exit_code, self.timed_out = stdout, stderr, exit_code, timed_out
    @property
    def success(self): return self.exit_code == 0 and not self.timed_out
    def to_dict(self):
        return dict(stdout=self.stdout, stderr=self.stderr, exit_code=self.exit_code,
                    timed_out=self.timed_out, success=self.success)


async def _command(*args):
    process = await asyncio.create_subprocess_exec('docker', *args, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL)
    try:
        return await asyncio.wait_for(process.wait(), 5)
    except BaseException:
        if process.returncode is None: process.kill()
        await process.wait()
        raise


async def check_docker_available():
    try: return await _command('info') == 0
    except (OSError, asyncio.TimeoutError): return False


async def run_code_in_sandbox(code, timeout=DEFAULT_TIMEOUT_SECONDS, input_data=None):
    if len(code.encode()) > 100000 or len((input_data or '').encode()) > 1000000:
        return SandboxResult('', 'Input exceeds execution limit', 1)
    if not await check_docker_available():
        return SandboxResult('', 'Isolated Docker worker unavailable', 125)
    name = 'kavach-' + uuid.uuid4().hex
    process = None
    output = {'stdout': bytearray(), 'stderr': bytearray()}
    readers = []
    async def read(stream, key):
        while chunk := await stream.read(4096):
            remaining = MAX_OUTPUT_BYTES - len(output[key])
            output[key].extend(chunk[:max(remaining, 0)])
            if len(chunk) > remaining: raise ValueError('Sandbox output limit exceeded')
    bootstrap = "import json,sys,io; p=json.load(sys.stdin); sys.stdin=io.StringIO(p['input']); exec(compile(p['code'],'generated.py','exec'),{'__name__':'__main__'})"
    try:
        process = await asyncio.create_subprocess_exec(
            'docker', 'run', '--name', name, '--rm', '--pull=never', '-i',
            '--network', 'none', '--read-only', '--cap-drop', 'ALL',
            '--security-opt', 'no-new-privileges', '--user', '65534:65534',
            '--cpus', '1', '--pids-limit', str(PIDS_LIMIT), '--memory', MEMORY_LIMIT, '--memory-swap', MEMORY_LIMIT,
            '--tmpfs', '/tmp:rw,noexec,nosuid,size=32m', '-w', '/tmp',
            SANDBOX_IMAGE, 'python', '-I', '-u', '-c', bootstrap,
            stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        async def execute():
            process.stdin.write(json.dumps({'code': code, 'input': input_data or ''}).encode())
            await process.stdin.drain()
            process.stdin.close()
            readers.extend([asyncio.create_task(read(process.stdout, 'stdout')), asyncio.create_task(read(process.stderr, 'stderr'))])
            await asyncio.gather(*readers)
            return await process.wait()
        exit_code = await asyncio.wait_for(execute(), max(1, min(timeout, 60)))
        return SandboxResult(output['stdout'].decode(errors='replace'), output['stderr'].decode(errors='replace'), exit_code)
    except asyncio.TimeoutError:
        return SandboxResult(output['stdout'].decode(errors='replace'), 'Execution timed out', 137, True)
    except (OSError, ValueError, BrokenPipeError) as exc:
        return SandboxResult(output['stdout'].decode(errors='replace'), str(exc), 125)
    finally:
        # Removing the named container kills the workload, not just the Docker client.
        try: await asyncio.shield(_command('rm', '-f', name))
        except (OSError, asyncio.TimeoutError): pass
        if process and process.returncode is None:
            process.kill()
            await process.wait()
        for reader in readers:
            if not reader.done(): reader.cancel()
        if readers: await asyncio.gather(*readers, return_exceptions=True)


async def verify_network_isolation():
    result = await run_code_in_sandbox("import socket\ntry:\n socket.create_connection(('1.1.1.1',443),timeout=2)\n print('FAIL')\nexcept OSError:\n print('BLOCKED')", timeout=10)
    return {'network_isolation_verified': result.success and result.stdout.strip() == 'BLOCKED', **result.to_dict()}
