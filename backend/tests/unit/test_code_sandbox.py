import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from app.services import code_sandbox as sandbox

class FakeProcess:
    def __init__(self,stdout=b'42\n',stderr=b'',exit_code=0):
        self.stdout=asyncio.StreamReader();self.stdout.feed_data(stdout);self.stdout.feed_eof()
        self.stderr=asyncio.StreamReader();self.stderr.feed_data(stderr);self.stderr.feed_eof()
        self.stdin=MagicMock();self.stdin.drain=AsyncMock()
        self.returncode=exit_code
    async def wait(self): return self.returncode
    def kill(self): self.returncode=137

@pytest.mark.asyncio
async def test_unavailable_worker_never_claims_execution():
    with patch.object(sandbox,'check_docker_available',AsyncMock(return_value=False)):
        result=await sandbox.run_code_in_sandbox('print(42)')
    assert not result.success and result.exit_code==125

@pytest.mark.asyncio
async def test_real_exit_status_flags_stdin_and_cleanup():
    process=FakeProcess(stderr=b'Expected failure',exit_code=1)
    with patch.object(sandbox,'check_docker_available',AsyncMock(return_value=True)), patch.object(sandbox.asyncio,'create_subprocess_exec',AsyncMock(return_value=process)) as spawn, patch.object(sandbox,'_command',AsyncMock(return_value=0)) as command:
        result=await sandbox.run_code_in_sandbox('raise RuntimeError()',input_data='payload')
    assert not result.success and result.stderr=='Expected failure'
    args=spawn.call_args.args
    for flag in ['--pull=never','--network','none','--read-only','--user','65534:65534','--cpus','--pids-limit','-i']: assert flag in args
    assert '-v' not in args
    command.assert_awaited_once()
    assert command.call_args.args[:2]==('rm','-f')
    assert b'payload' in process.stdin.write.call_args.args[0]

@pytest.mark.asyncio
async def test_output_is_bounded_while_reading():
    process=FakeProcess(stdout=b'x'*(sandbox.MAX_OUTPUT_BYTES+4096))
    with patch.object(sandbox,'check_docker_available',AsyncMock(return_value=True)), patch.object(sandbox.asyncio,'create_subprocess_exec',AsyncMock(return_value=process)), patch.object(sandbox,'_command',AsyncMock(return_value=0)) as cleanup:
        result=await sandbox.run_code_in_sandbox('print("many")')
    assert len(result.stdout.encode())<=sandbox.MAX_OUTPUT_BYTES
    assert not result.success and 'output limit' in result.stderr
    cleanup.assert_awaited_once()

@pytest.mark.asyncio
async def test_timeout_removes_container():
    process=FakeProcess();process.stdout=asyncio.StreamReader();process.returncode=None
    with patch.object(sandbox,'check_docker_available',AsyncMock(return_value=True)), patch.object(sandbox.asyncio,'create_subprocess_exec',AsyncMock(return_value=process)), patch.object(sandbox,'_command',AsyncMock(return_value=0)) as cleanup:
        result=await sandbox.run_code_in_sandbox('while True: pass',timeout=1)
    assert result.timed_out and not result.success
    cleanup.assert_awaited_once()

@pytest.mark.asyncio
async def test_network_probe_requires_successful_execution():
    with patch.object(sandbox,'run_code_in_sandbox',AsyncMock(return_value=sandbox.SandboxResult('BLOCKED','',1))):
        assert not (await sandbox.verify_network_isolation())['network_isolation_verified']
