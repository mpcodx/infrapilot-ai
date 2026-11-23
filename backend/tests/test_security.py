import pytest
from backend.app.security.auditor import SecurityAuditor


def test_security_audit_run():
    sample_ports = [
        {"protocol": "tcp", "local_address": "0.0.0.0", "local_port": 21, "status": "LISTEN"},
        {"protocol": "tcp", "local_address": "127.0.0.1", "local_port": 8000, "status": "LISTEN"},
    ]
    findings = SecurityAuditor.run_full_audit(ports=sample_ports)
    assert isinstance(findings, list)
    assert len(findings) > 0

    # Ensure required finding schema fields are present
    f = findings[0]
    assert "finding_id" in f
    assert "severity" in f
    assert "title" in f
    assert "description" in f
    assert "affected_component" in f
    assert "recommended_fix" in f


def test_listening_ports_audit():
    risky_ports = [
        {"protocol": "tcp", "local_address": "0.0.0.0", "local_port": 6379, "status": "LISTEN", "process_name": "redis"},
    ]
    findings = SecurityAuditor.audit_listening_ports(risky_ports)
    assert len(findings) == 1
    assert findings[0]["severity"] == "High"
    assert "Redis" in findings[0]["title"]
