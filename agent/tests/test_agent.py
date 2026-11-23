import pytest
from unittest.mock import patch, MagicMock
from agent.piops_agent.client import InfraPilotAgent, PIopsAgent


def test_agent_alias():
    assert PIopsAgent is InfraPilotAgent


def test_agent_collect_metrics():
    agent = InfraPilotAgent(backend_url="http://127.0.0.1:8000", shared_secret="test-secret")
    metrics = agent.collect_metrics()
    assert "hostname" in metrics
    assert "cpu_percent" in metrics
    assert "ram_percent" in metrics
    assert "disk_percent" in metrics
    assert 0 <= metrics["cpu_percent"] <= 100


@patch("requests.post")
def test_agent_register(mock_post):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"agent_id": "AGENT-12345", "token": "tok-abcde", "status": "registered"}
    mock_post.return_value = mock_resp

    agent = InfraPilotAgent(backend_url="http://127.0.0.1:8000", shared_secret="test-secret")
    success = agent.register()
    assert success is True
    assert agent.agent_id == "AGENT-12345"
    assert agent.auth_token == "tok-abcde"


@patch("requests.post")
def test_agent_heartbeat(mock_post):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_post.return_value = mock_resp

    agent = InfraPilotAgent(backend_url="http://127.0.0.1:8000", shared_secret="test-secret")
    agent.agent_id = "AGENT-12345"
    agent.auth_token = "tok-abcde"

    success = agent.send_heartbeat()
    assert success is True
