"""
Unit tests for the EgressMonitor sovereignty proof module.
Tests: socket audit logging, Ollama host validation, idempotency, and reporting.
"""

import socket
import pytest
from unittest.mock import patch, MagicMock
from app.middleware.egress_monitor import EgressMonitor, EgressEntry

# Capture the truly original socket.getaddrinfo before any test patches it
_ORIGINAL_GETADDRINFO = socket.getaddrinfo


@pytest.fixture(autouse=True)
def restore_socket():
    """Restore socket.getaddrinfo to its original state after every test."""
    yield
    socket.getaddrinfo = _ORIGINAL_GETADDRINFO


@pytest.fixture
def monitor():
    """Fresh EgressMonitor instance with clean socket state."""
    # Ensure we start from un-patched state
    socket.getaddrinfo = _ORIGINAL_GETADDRINFO
    m = EgressMonitor()
    yield m


class TestOllamaHostValidation:
    """Tests for validate_ollama_host() sovereignty checks."""

    def test_local_ollama_host_passes(self, monitor):
        """Valid localhost Ollama host should not raise."""
        monitor.validate_ollama_host("http://localhost:11434")

    def test_127_host_passes(self, monitor):
        """127.0.0.1 should be accepted as local."""
        monitor.validate_ollama_host("http://127.0.0.1:11434")

    def test_docker_internal_passes(self, monitor):
        """host.docker.internal is a deployment exception."""
        monitor.validate_ollama_host("http://host.docker.internal:11434")

    def test_ollama_service_name_passes(self, monitor):
        """'ollama' as hostname is a deployment exception (Docker Compose)."""
        monitor.validate_ollama_host("http://ollama:11434")

    def test_external_host_raises(self, monitor):
        """External API hosts must raise RuntimeError."""
        with pytest.raises(RuntimeError, match="SOVEREIGNTY VIOLATION"):
            monitor.validate_ollama_host("http://api.openai.com:443")

    def test_external_cloud_host_raises(self, monitor):
        """Cloud LLM endpoints must be rejected."""
        with pytest.raises(RuntimeError, match="SOVEREIGNTY VIOLATION"):
            monitor.validate_ollama_host("https://api.anthropic.com/v1")

    def test_non_loopback_resolution_raises(self, monitor):
        """Host that resolves to non-loopback IP should raise."""
        with patch("socket.gethostbyname", return_value="192.168.1.100"):
            with pytest.raises(RuntimeError, match="not loopback"):
                monitor.validate_ollama_host("http://localhost:11434")

    def test_gaierror_is_tolerated(self, monitor):
        """DNS resolution failure is acceptable in air-gapped environments."""
        with patch("socket.gethostbyname", side_effect=socket.gaierror):
            # Should not raise — gaierror is silently caught
            monitor.validate_ollama_host("http://localhost:11434")


class TestSocketAudit:
    """Tests for install_socket_audit() socket patching."""

    def test_socket_audit_logs_local_connections(self, monitor):
        """After patching, local DNS lookups should appear in logs."""
        monitor.install_socket_audit()

        # Trigger a DNS lookup for localhost
        try:
            socket.getaddrinfo("localhost", 80)
        except Exception:
            pass  # Resolution may fail in test environments

        assert len(monitor.logs) >= 1
        entry = monitor.logs[-1]
        assert entry.destination == "localhost:80"
        assert entry.classification == "LOCAL_ALLOWED"
        assert entry.method == "DNS_LOOKUP"

    def test_socket_audit_logs_127_as_local(self, monitor):
        """127.x.x.x addresses should be classified as LOCAL_ALLOWED."""
        monitor.install_socket_audit()

        try:
            socket.getaddrinfo("127.0.0.1", 443)
        except Exception:
            pass

        matching = [e for e in monitor.logs if e.destination == "127.0.0.1:443"]
        assert len(matching) >= 1
        assert matching[-1].classification == "LOCAL_ALLOWED"

    def test_socket_audit_logs_external_as_recorded(self, monitor):
        """Non-local hosts should be classified as EXTERNAL_RECORDED."""
        monitor.install_socket_audit()

        try:
            socket.getaddrinfo("example.com", 443)
        except Exception:
            pass

        matching = [e for e in monitor.logs if "example.com" in e.destination]
        assert len(matching) >= 1
        assert matching[-1].classification == "EXTERNAL_RECORDED"

    def test_audit_idempotent(self, monitor):
        """Calling install_socket_audit() twice should not double-patch."""
        monitor.install_socket_audit()
        first_func = socket.getaddrinfo

        monitor.install_socket_audit()
        second_func = socket.getaddrinfo

        # Should be the exact same patched function
        assert first_func is second_func

    def test_connection_counter_increments(self, monitor):
        """Each DNS lookup should increment the connection counter."""
        monitor.install_socket_audit()
        initial = monitor._attempted_connections

        try:
            socket.getaddrinfo("localhost", 80)
        except Exception:
            pass

        assert monitor._attempted_connections == initial + 1

    def test_log_entry_has_timestamp(self, monitor):
        """Each log entry should have an ISO format timestamp."""
        monitor.install_socket_audit()

        try:
            socket.getaddrinfo("localhost", 80)
        except Exception:
            pass

        assert len(monitor.logs) >= 1
        entry = monitor.logs[-1]
        assert entry.timestamp  # Non-empty
        assert "T" in entry.timestamp  # ISO format contains T separator


class TestSovereigntyReport:
    """Tests for get_sovereignty_report() summary generation."""

    def test_empty_report(self, monitor):
        """Fresh monitor should report zero connections and sovereign=True."""
        report = monitor.get_sovereignty_report()
        assert report["total_connections"] == 0
        assert report["local_allowed"] == 0
        assert report["external_recorded"] == 0
        assert report["sovereign"] is True

    def test_report_with_local_entries(self, monitor):
        """Report with only local entries should be sovereign."""
        monitor.logs.append(EgressEntry(
            destination="localhost:11434",
            classification="LOCAL_ALLOWED",
            method="DNS_LOOKUP",
            path="socket.getaddrinfo",
            latency_ms=0, port=11434,
            timestamp="2026-01-01T00:00:00",
            model_used=None,
        ))
        monitor._attempted_connections = 1

        report = monitor.get_sovereignty_report()
        assert report["local_allowed"] == 1
        assert report["external_recorded"] == 0
        assert report["sovereign"] is True

    def test_report_with_external_entries(self, monitor):
        """Report with any external entry should not be sovereign."""
        monitor.logs.append(EgressEntry(
            destination="api.openai.com:443",
            classification="EXTERNAL_RECORDED",
            method="DNS_LOOKUP",
            path="socket.getaddrinfo",
            latency_ms=0, port=443,
            timestamp="2026-01-01T00:00:00",
            model_used=None,
        ))
        monitor._attempted_connections = 1

        report = monitor.get_sovereignty_report()
        assert report["external_recorded"] == 1
        assert report["sovereign"] is False
        assert "api.openai.com:443" in report["external_destinations"]

    def test_clear_logs_resets_state(self, monitor):
        """clear_logs() should reset all counters and logs."""
        monitor.logs.append(EgressEntry(
            destination="localhost:80",
            classification="LOCAL_ALLOWED",
            method="DNS_LOOKUP",
            path="socket.getaddrinfo",
            latency_ms=0, port=80,
            timestamp="2026-01-01T00:00:00",
            model_used=None,
        ))
        monitor._attempted_connections = 5

        monitor.clear_logs()
        assert len(monitor.logs) == 0
        assert monitor._attempted_connections == 0
