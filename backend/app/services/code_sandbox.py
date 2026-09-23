"""
KavachAI — Docker Code Sandbox
Implements: Phase 3.1 — Isolated container execution for analysis scripts.

Security constraints:
  - --cap-drop ALL (no Linux capabilities)
  - --security-opt no-new-privileges
  - --pids-limit 100 (fork bomb protection)
  - --memory 256m (OOM protection)
  - --network none (network isolation)
  - Read-only root filesystem with tmpfs /tmp

Only used for running deterministic analysis scripts in a restricted environment.
"""

import asyncio
import logging
import tempfile
import os
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger("kavachai.sandbox")

# Execution limits
DEFAULT_TIMEOUT_SECONDS = 30
MAX_OUTPUT_BYTES = 65536  # 64 KB output cap
MEMORY_LIMIT = "256m"
PIDS_LIMIT = 100
SANDBOX_IMAGE = "python:3.12-slim"


class SandboxResult:
    """Result of a sandboxed code execution."""

    def __init__(
        self,
        stdout: str,
        stderr: str,
        exit_code: int,
        timed_out: bool = False,
    ):
        self.stdout = stdout
        self.stderr = stderr
        self.exit_code = exit_code
        self.timed_out = timed_out

    @property
    def success(self) -> bool:
        return self.exit_code == 0 and not self.timed_out

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stdout": self.stdout,
            "stderr": self.stderr,
            "exit_code": self.exit_code,
            "timed_out": self.timed_out,
            "success": self.success,
        }


async def check_docker_available() -> bool:
    """Check if Docker daemon is reachable."""
    try:
        proc = await asyncio.create_subprocess_exec(
            "docker", "info",
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        await proc.wait()
        return proc.returncode == 0
    except FileNotFoundError:
        logger.warning("Docker binary not found on PATH")
        return False
    except Exception as e:
        logger.warning("Docker availability check failed: %s", e)
        return False


async def run_code_in_sandbox(
    code: str,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
    input_data: Optional[str] = None,
) -> SandboxResult:
    """
    Execute Python code in an isolated Docker container.

    Security layers:
      1. --cap-drop ALL: removes all Linux capabilities
      2. --security-opt no-new-privileges: prevents privilege escalation
      3. --pids-limit: limits process count (fork bomb protection)
      4. --memory: hard memory cap
      5. --network none: no network access at all
      6. --read-only + tmpfs: read-only rootfs with writable /tmp

    Args:
        code: Python source code to execute
        timeout: maximum execution time in seconds
        input_data: optional stdin data

    Returns:
        SandboxResult with stdout, stderr, exit_code, timed_out
    """
    if not await check_docker_available():
        logger.error("Docker is not available — sandbox execution aborted")
        return SandboxResult(
            stdout="",
            stderr="Docker is not available. Cannot execute code in sandbox.",
            exit_code=1,
            timed_out=False,
        )

    # Write code to a temp file that will be mounted read-only
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False, prefix="kavach_sandbox_"
    ) as f:
        f.write(code)
        script_path = f.name

    try:
        # Build the docker run command with all security constraints
        cmd = [
            "docker", "run",
            "--rm",                                       # Auto-remove container
            "--cap-drop", "ALL",                          # No Linux capabilities
            "--security-opt", "no-new-privileges",        # No privilege escalation
            "--pids-limit", str(PIDS_LIMIT),              # Fork bomb protection
            "--memory", MEMORY_LIMIT,                     # OOM protection
            "--network", "none",                          # Network isolation
            "--read-only",                                # Read-only root filesystem
            "--tmpfs", "/tmp:rw,noexec,nosuid,size=64m",  # Writable temp space
            "-v", f"{script_path}:/sandbox/script.py:ro", # Mount script read-only
            "-w", "/sandbox",
            SANDBOX_IMAGE,
            "python", "/sandbox/script.py",
        ]

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            stdin=asyncio.subprocess.PIPE if input_data else asyncio.subprocess.DEVNULL,
        )

        try:
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                proc.communicate(input=input_data.encode() if input_data else None),
                timeout=timeout,
            )
            return SandboxResult(
                stdout=stdout_bytes.decode("utf-8", errors="replace")[:MAX_OUTPUT_BYTES],
                stderr=stderr_bytes.decode("utf-8", errors="replace")[:MAX_OUTPUT_BYTES],
                exit_code=proc.returncode or 0,
                timed_out=False,
            )
        except asyncio.TimeoutError:
            # Kill the container on timeout
            proc.kill()
            await proc.wait()
            return SandboxResult(
                stdout="",
                stderr=f"Execution timed out after {timeout} seconds",
                exit_code=137,
                timed_out=True,
            )

    except Exception as e:
        logger.exception("Sandbox execution failed: %s", e)
        return SandboxResult(
            stdout="",
            stderr=f"Sandbox execution error: {str(e)}",
            exit_code=1,
            timed_out=False,
        )
    finally:
        # Clean up temp script file
        try:
            os.unlink(script_path)
        except OSError:
            pass


async def verify_network_isolation() -> Dict[str, Any]:
    """
    Verify that network isolation works by attempting a network call from a sandbox.
    Returns a report dict suitable for sovereignty audit.
    """
    test_code = """
import socket
try:
    socket.create_connection(("8.8.8.8", 53), timeout=3)
    print("FAIL: Network access succeeded — isolation BROKEN")
except (OSError, socket.timeout):
    print("PASS: Network access blocked — isolation VERIFIED")
"""
    result = await run_code_in_sandbox(test_code, timeout=10)
    isolated = "PASS" in result.stdout
    return {
        "network_isolation_verified": isolated,
        "stdout": result.stdout.strip(),
        "exit_code": result.exit_code,
    }
