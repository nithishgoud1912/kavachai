"""Process-scoped network policy and observed socket events, not air-gap certification."""
import ipaddress
import socket
import sys
from collections import deque
from datetime import datetime, timezone
from urllib.parse import urlparse
from app.config import settings

from pydantic import BaseModel
class EgressEntry(BaseModel):
    destination: str
    classification: str
    method: str
    path: str
    latency_ms: float
    port: int
    timestamp: str
    model_used: str | None = None

class EgressMonitor:
    def __init__(self):
        self.logs = deque(maxlen=1000)
        self.total = self.blocked = self.allowed = 0
        self.started = datetime.now(timezone.utc).isoformat()
        self.installed = False
        self.hosts = set(settings.ALLOWED_INFERENCE_HOSTS.split(',')) | {'localhost','127.0.0.1','::1'}
        self.ips = {'127.0.0.1','::1'}
    def validate_ollama_host(self, value):
        if urlparse(value).hostname not in self.hosts: raise RuntimeError('Inference host is not allowed')
    def install_socket_audit(self):
        if self.installed: return
        self.validate_ollama_host(settings.OLLAMA_HOST)
        # Resolve only operator-configured hosts before installing the hook.
        import os
        docker_host = urlparse(os.environ.get('DOCKER_HOST', ''))
        if docker_host.hostname: self.hosts.add(docker_host.hostname)
        for host in self.hosts:
            try:
                for result in socket.getaddrinfo(host, None):
                    address = ipaddress.ip_address(result[4][0])
                    if not (address.is_private or address.is_loopback):
                        raise RuntimeError('Allowed endpoint resolves outside private infrastructure')
                    self.ips.add(str(address))
            except socket.gaierror:
                continue
        def audit(event, args):
            def _norm_host(val):
                if isinstance(val, (bytes, bytearray)):
                    return val.decode("utf-8", "ignore")
                return str(val).strip()

            if event == 'socket.connect':
                sock, destination = args
                if sock.family not in (socket.AF_INET, socket.AF_INET6): return
                host, port = _norm_host(destination[0]), destination[1]
                permitted = host in self.ips or host in self.hosts
            elif event == 'socket.getaddrinfo':
                host, port = _norm_host(args[0]), args[1] or 0
                permitted = host in self.hosts or host in self.ips
            else: return
            if not permitted:
                service = 'Unauthorized External Egress Attempt'
            elif port == 11434 or 'ollama' in host:
                service = 'Ollama Inference Runtime (Reasoning / Coder / Vision)'
            elif port in (8000, 8080) or '8000' in str(port):
                service = 'FastAPI Application API'
            elif port in (3000, 3001) or '3000' in str(port):
                service = 'Next.js Workbench UI'
            elif port == 5432:
                service = 'Local Database (pgvector / SQLite)'
            else:
                service = 'Local Loopback IPC'

            self.total += 1
            if permitted: self.allowed += 1
            else: self.blocked += 1
            self.logs.append(dict(id=str(self.total),timestamp=datetime.now(timezone.utc).isoformat(),destination=host,port=port,
                                  service=service,method=event,status='allowed' if permitted else 'blocked',latency_ms=0.1))
            if not permitted: raise PermissionError('Network destination denied by local policy')
        sys.addaudithook(audit)
        self.installed = True
    def get_sovereignty_report(self):
        is_sovereign = bool(self.blocked == 0 and self.installed)
        return dict(total_connections=self.total,local_allowed=self.allowed,external_recorded=self.blocked,
                    external_destinations=sorted({e['destination'] for e in self.logs if e['status']=='blocked'}),
                    sovereign=is_sovereign,verified_airgap=False,airgap_status="active_enforced" if self.installed else "uninitialized",
                    session_start=self.started,allowlist=sorted(self.hosts),
                    observer_active=self.installed,scope='Python backend socket events only; browser, native libraries, workers and host require independent monitoring',
                    observed_at=datetime.now(timezone.utc).isoformat(),log_entries=len(self.logs))
    def clear_logs(self):
        self.logs.clear()
        self.total=self.blocked=self.allowed=0

egress_monitor = EgressMonitor()
