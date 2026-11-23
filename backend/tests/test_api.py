import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_health_endpoint():
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"


def test_system_metrics_endpoint():
    res = client.get("/api/v1/system/metrics")
    assert res.status_code == 200
    data = res.json()
    assert "cpu_percent" in data
    assert "ram_percent" in data


def test_discovery_endpoints():
    res_proc = client.get("/api/v1/processes?limit=5")
    assert res_proc.status_code == 200
    assert isinstance(res_proc.json(), list)

    res_ports = client.get("/api/v1/ports")
    assert res_ports.status_code == 200
    assert isinstance(res_ports.json(), list)


def test_security_findings_endpoint():
    res = client.get("/api/v1/security/findings")
    assert res.status_code == 200
    findings = res.json()
    assert isinstance(findings, list)


def test_action_preview_and_approve_api():
    # Preview
    prev_res = client.post("/api/v1/actions/preview", json={"action_type": "disk_free", "target": "/"})
    assert prev_res.status_code == 200
    prev_data = prev_res.json()
    action_id = prev_data["action_id"]

    # Approve
    appr_res = client.post("/api/v1/actions/approve", json={"action_id": action_id, "confirmed": True})
    assert appr_res.status_code == 200
    appr_data = appr_res.json()
    assert appr_data["status"] == "completed"
