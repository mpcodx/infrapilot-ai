import pytest
from backend.app.services.action_engine import SafeActionEngine


def test_action_preview_valid():
    preview = SafeActionEngine.create_preview(action_type="disk_free", target="/")
    assert preview["action_id"].startswith("ACT-")
    assert preview["requires_approval"] is True
    assert preview["command_preview"] == "df -h /"


def test_command_injection_prevention():
    with pytest.raises(ValueError, match="illegal characters"):
        SafeActionEngine.create_preview(action_type="disk_free", target="/; rm -rf /")

    with pytest.raises(ValueError, match="illegal characters"):
        SafeActionEngine.create_preview(action_type="disk_free", target="test && cat /etc/shadow")


def test_unsupported_action_rejection():
    with pytest.raises(ValueError, match="not supported"):
        SafeActionEngine.create_preview(action_type="arbitrary_bash", target="localhost")


def test_action_execution_flow():
    preview = SafeActionEngine.create_preview(action_type="disk_free", target="/")
    action_id = preview["action_id"]

    result = SafeActionEngine.execute_approved_action(action_id)
    assert result["status"] == "completed"
    assert "Filesystem" in result["output"] or "/" in result["output"]
