"""
KavachAI Egress Monitor — Sovereignty Proof via Socket Audit
Implements: NFR-SEC-1 (Air-gap evidence), NFR-SOV-1 (No external API calls)

Provides audit-level evidence that all network calls remain local.
Instead of disruptive system-wide firewall rules, this module patches
socket.getaddrinfo to log and classify every DNS resolution attempt.
"""

import socket
from urllib.parse import urlparse
from pydantic import BaseModel
from datetime import datetime, timezone
from typing import Optional


class EgressEntry(BaseModel):
    """A single logged network resolution attempt."""
    destination: str
    classification: str  # LOCAL_ALLOWED | EXTERNAL_RECORDED
    method: str
    path: str
    latency_ms: float
    port: int
    timestamp: str
    model_used: Optional[str]


class EgressMonitor:
    """
    Monitors and audits all outgoing network connections.

    - validate_ollama_host(): Ensures the configured Ollama endpoint is localhost.
    - install_socket_audit(): Patches socket.getaddrinfo to log every DNS lookup.

    Safety: Does NOT block connections — only records them for sovereignty proof.
    Air-gapping is enforced via physical disconnection + Docker `internal: true`.
    """

    LOCAL_HOSTS = {"localhost", "127.0.0.1"}
    DEPLOYMENT_EXCEPTIONS = {"ollama", "host.docker.internal"}

    def __init__(self):
        self.logs: list[EgressEntry] = []
        self._attempted_connections = 0

    def validate_ollama_host(self, ollama_host: str) -> None:
        """
        Validate that the OLLAMA_HOST setting points to a local address.
        Raises RuntimeError if the host resolves to a non-loopback address.
        """
        parsed = urlparse(ollama_host)
        host = parsed.hostname or ""
        if host not in self.LOCAL_HOSTS and host not in self.DEPLOYMENT_EXCEPTIONS:
            raise RuntimeError(
                f"SOVEREIGNTY VIOLATION: OLLAMA_HOST={ollama_host} is not local."
            )
        try:
            resolved_ip = socket.gethostbyname(host)
            if not resolved_ip.startswith("127.") and resolved_ip != "::1":
                raise RuntimeError(
                    f"OLLAMA_HOST resolves to {resolved_ip}, not loopback."
                )
        except socket.gaierror:
            # Unable to resolve — acceptable in air-gapped environments
            pass

    def install_socket_audit(self) -> None:
        """
        Monkey-patch socket.getaddrinfo to log all DNS resolution attempts.
        Idempotent — calling multiple times will not double-patch.
        """
        if getattr(socket.getaddrinfo, "_kavach_patched", False):
            return
        original = socket.getaddrinfo
        monitor = self

        def audited(host, port, *a, **kw):
            monitor._attempted_connections += 1
            is_local = (
                str(host) in monitor.LOCAL_HOSTS
                or str(host).startswith("127.")
            )
            monitor.logs.append(EgressEntry(
                destination=f"{host}:{port}",
                classification="LOCAL_ALLOWED" if is_local else "EXTERNAL_RECORDED",
                method="DNS_LOOKUP",
                path="socket.getaddrinfo",
                latency_ms=0,
                port=port or 0,
                timestamp=datetime.now(timezone.utc).isoformat(),
                model_used=None,
            ))
            return original(host, port, *a, **kw)

        audited._kavach_patched = True
        socket.getaddrinfo = audited

    def get_sovereignty_report(self) -> dict:
        """
        Generate a sovereignty compliance report from collected logs.
        Returns summary of local vs external connection attempts.
        """
        local_count = sum(
            1 for e in self.logs if e.classification == "LOCAL_ALLOWED"
        )
        external_count = sum(
            1 for e in self.logs if e.classification == "EXTERNAL_RECORDED"
        )
        external_destinations = list(set(
            e.destination for e in self.logs
            if e.classification == "EXTERNAL_RECORDED"
        ))
        return {
            "total_connections": self._attempted_connections,
            "local_allowed": local_count,
            "external_recorded": external_count,
            "external_destinations": external_destinations,
            "sovereign": external_count == 0,
            "log_entries": len(self.logs),
        }

    def clear_logs(self) -> None:
        """Reset audit logs (useful for testing)."""
        self.logs.clear()
        self._attempted_connections = 0


# Module-level singleton — shared across the application
egress_monitor = EgressMonitor()
