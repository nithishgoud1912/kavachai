"""Use a subprocess because CPython audit hooks cannot be removed safely."""
import os
import subprocess
import sys
import pytest
from app.middleware.egress_monitor import EgressMonitor

@pytest.mark.parametrize('host',['https://example.com','http://8.8.8.8','https://api.openai.com'])
def test_external_model_host_rejected(host):
    with pytest.raises(RuntimeError): EgressMonitor().validate_ollama_host(host)

@pytest.mark.parametrize('host',['http://localhost:11434','http://127.0.0.1:11434','http://ollama:11434'])
def test_configured_private_host_allowed(host):
    EgressMonitor().validate_ollama_host(host)

def test_empty_observation_is_not_certification():
    report=EgressMonitor().get_sovereignty_report()
    assert report['total_connections']==0 and report['verified_airgap'] is False and report['observer_active'] is False

def test_external_dns_and_literal_ip_are_blocked_before_network():
    code="""
import socket
from app.middleware.egress_monitor import EgressMonitor
m=EgressMonitor();m.install_socket_audit()
for operation in [lambda:socket.getaddrinfo('unapproved.invalid',443),lambda:socket.socket().connect(('8.8.8.8',443))]:
    try: operation()
    except PermissionError: pass
    else: raise AssertionError('Unapproved network operation allowed')
assert m.get_sovereignty_report()['external_recorded']==2
assert not m.get_sovereignty_report()['verified_airgap']
"""
    from pathlib import Path
    result=subprocess.run([sys.executable,'-c',code],cwd=Path(__file__).resolve().parents[2],capture_output=True,text=True,timeout=15)
    assert result.returncode==0,result.stderr
