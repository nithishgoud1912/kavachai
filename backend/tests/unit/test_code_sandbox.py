"""
KavachAI — Unit Tests: Docker Code Sandbox
Tests the sandbox execution, security constraints, and network isolation.
All tests use mocking to avoid needing a live Docker daemon.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.code_sandbox import (
    SandboxResult,
    check_docker_available,
    run_code_in_sandbox,
    verify_network_isolation,
    DEFAULT_TIMEOUT_SECONDS,
    MEMORY_LIMIT,
    PIDS_LIMIT,
)


# ---------------------------------------------------------------------------
# SandboxResult Tests
# ---------------------------------------------------------------------------

class TestSandboxResult:

    def test_success_on_exit_zero(self):
        result = SandboxResult(stdout="output", stderr="", exit_code=0)
        assert result.success is True

    def test_failure_on_nonzero_exit(self):
        result = SandboxResult(stdout="", stderr="error", exit_code=1)
        assert result.success is False

    def test_failure_on_timeout(self):
        result = SandboxResult(stdout="", stderr="", exit_code=0, timed_out=True)
        assert result.success is False

    def test_to_dict(self):
        result = SandboxResult(stdout="hello", stderr="", exit_code=0, timed_out=False)
        d = result.to_dict()
        assert d["stdout"] == "hello"
        assert d["exit_code"] == 0
        assert d["success"] is True
        assert d["timed_out"] is False


# ---------------------------------------------------------------------------
# Docker Availability Tests
# ---------------------------------------------------------------------------

class TestDockerAvailable:

    @pytest.mark.asyncio
    async def test_docker_available_success(self):
        mock_proc = AsyncMock()
        mock_proc.returncode = 0
        mock_proc.wait = AsyncMock()
        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            available = await check_docker_available()
            assert available is True

    @pytest.mark.asyncio
    async def test_docker_not_available(self):
        with patch("asyncio.create_subprocess_exec", side_effect=FileNotFoundError):
            available = await check_docker_available()
            assert available is False


# ---------------------------------------------------------------------------
# Sandbox Execution Tests
# ---------------------------------------------------------------------------

class TestRunCodeInSandbox:

    @pytest.mark.asyncio
    async def test_run_without_docker(self):
        """Running code when Docker is unavailable should return graceful error."""
        with patch(
            "app.services.code_sandbox.check_docker_available",
            new_callable=AsyncMock,
            return_value=False,
        ):
            result = await run_code_in_sandbox("print('hello')")
            assert result.success is False
            assert "not available" in result.stderr.lower()

    @pytest.mark.asyncio
    async def test_successful_execution(self):
        """Successful code execution returns stdout."""
        mock_proc = AsyncMock()
        mock_proc.communicate = AsyncMock(return_value=(b"hello\n", b""))
        mock_proc.returncode = 0
        mock_proc.kill = AsyncMock()

        with patch(
            "app.services.code_sandbox.check_docker_available",
            new_callable=AsyncMock,
            return_value=True,
        ):
            with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
                with patch("asyncio.wait_for", return_value=(b"hello\n", b"")):
                    # Override communicate to work within wait_for mock
                    mock_proc.communicate = AsyncMock(return_value=(b"hello\n", b""))
                    result = await run_code_in_sandbox("print('hello')")
                    assert result.stdout.strip() == "hello"
                    assert result.exit_code == 0


# ---------------------------------------------------------------------------
# Security Constraint Tests
# ---------------------------------------------------------------------------

class TestSecurityConstraints:

    def test_default_timeout(self):
        assert DEFAULT_TIMEOUT_SECONDS == 30

    def test_memory_limit(self):
        assert MEMORY_LIMIT == "256m"

    def test_pids_limit(self):
        assert PIDS_LIMIT == 100


# ---------------------------------------------------------------------------
# Network Isolation Tests
# ---------------------------------------------------------------------------

class TestNetworkIsolation:

    @pytest.mark.asyncio
    async def test_verify_network_isolation_pass(self):
        """Network isolation test should report PASS when sandbox blocks network."""
        mock_result = SandboxResult(
            stdout="PASS: Network access blocked — isolation VERIFIED",
            stderr="",
            exit_code=0,
        )
        with patch(
            "app.services.code_sandbox.run_code_in_sandbox",
            new_callable=AsyncMock,
            return_value=mock_result,
        ):
            report = await verify_network_isolation()
            assert report["network_isolation_verified"] is True

    @pytest.mark.asyncio
    async def test_verify_network_isolation_fail(self):
        """Network isolation test should report FAIL when sandbox allows network."""
        mock_result = SandboxResult(
            stdout="FAIL: Network access succeeded — isolation BROKEN",
            stderr="",
            exit_code=0,
        )
        with patch(
            "app.services.code_sandbox.run_code_in_sandbox",
            new_callable=AsyncMock,
            return_value=mock_result,
        ):
            report = await verify_network_isolation()
            assert report["network_isolation_verified"] is False
