import re
import uuid
import datetime
import subprocess
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("infrapilot-action-engine")


class SafeActionEngine:
    ALLOWED_ACTIONS = {
        "restart_container": {
            "template": ["docker", "restart", "{target}"],
            "risk": "Medium",
            "desc": "Restart the specified Docker container.",
        },
        "stop_container": {
            "template": ["docker", "stop", "{target}"],
            "risk": "High",
            "desc": "Stop the specified Docker container gracefully.",
        },
        "start_container": {
            "template": ["docker", "start", "{target}"],
            "risk": "Low",
            "desc": "Start the specified stopped Docker container.",
        },
        "systemd_status": {
            "template": ["systemctl", "status", "{target}", "--no-pager"],
            "risk": "Low",
            "desc": "Inspect status of systemd service (read-only).",
        },
        "docker_logs": {
            "template": ["docker", "logs", "--tail", "50", "{target}"],
            "risk": "Low",
            "desc": "View last 50 log lines of container (read-only).",
        },
        "disk_free": {
            "template": ["df", "-h", "{target}"],
            "risk": "Low",
            "desc": "Check disk partition free space (read-only).",
        },
    }

    ACTION_TTL_SECONDS = 300  # 5 minutes expiry for unapproved actions
    _pending_actions: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def validate_target(cls, target: str) -> bool:
        """Validate target against strict alphanumeric regex to prevent injection."""
        if not target or len(target) > 100:
            return False
        # Allow only alphanumeric, hyphen, underscore, slash, dot
        return bool(re.match(r'^[a-zA-Z0-9_\-\./]+$', target))

    @classmethod
    def create_preview(cls, action_type: str, target: str) -> Dict[str, Any]:
        if action_type not in cls.ALLOWED_ACTIONS:
            logger.warning(f"Rejected unsupported action type: {action_type}")
            raise ValueError(f"Action type '{action_type}' is not supported or permitted.")

        if not cls.validate_target(target):
            logger.warning(f"Rejected target containing invalid characters: {target}")
            raise ValueError("Target contains illegal characters. Only alphanumeric, hyphens, and dots allowed.")

        spec = cls.ALLOWED_ACTIONS[action_type]
        action_id = f"ACT-{uuid.uuid4().hex[:8]}"
        cmd_tokens = [t.format(target=target) for t in spec["template"]]
        preview_str = " ".join(cmd_tokens)

        now = datetime.datetime.now(datetime.timezone.utc)
        expires_at = now + datetime.timedelta(seconds=cls.ACTION_TTL_SECONDS)

        record = {
            "action_id": action_id,
            "action_type": action_type,
            "target": target,
            "cmd_tokens": cmd_tokens,
            "command_preview": preview_str,
            "risk_level": spec["risk"],
            "description": spec["desc"],
            "requested_at": now.isoformat(),
            "expires_at": expires_at.isoformat(),
            "status": "pending_approval",
        }

        cls._pending_actions[action_id] = record
        logger.info(f"Created action preview: {action_id} ({action_type} on {target})")
        return {
            "action_id": action_id,
            "action_type": action_type,
            "target": target,
            "command_preview": preview_str,
            "risk_level": spec["risk"],
            "description": spec["desc"],
            "expires_at": expires_at.isoformat(),
            "requires_approval": True,
        }

    @classmethod
    def execute_approved_action(cls, action_id: str) -> Dict[str, Any]:
        if action_id not in cls._pending_actions:
            logger.warning(f"Attempted execution of unknown or purged action: {action_id}")
            raise ValueError("Action ID not found or already executed.")

        action = cls._pending_actions[action_id]
        if action["status"] != "pending_approval":
            logger.warning(f"Replay attempt or invalid status for {action_id}: {action['status']}")
            raise ValueError(f"Action status is '{action['status']}', cannot execute (replay protection enforced).")

        # Check expiration
        now = datetime.datetime.now(datetime.timezone.utc)
        expires_at = datetime.datetime.fromisoformat(action["expires_at"])
        if now > expires_at:
            action["status"] = "expired"
            logger.warning(f"Action confirmation expired for {action_id}")
            raise ValueError("Action confirmation has expired (5-minute TTL exceeded).")

        cmd_tokens = action["cmd_tokens"]

        try:
            logger.info(f"Executing approved action: {action_id} -> {cmd_tokens}")
            res = subprocess.run(
                cmd_tokens,
                capture_output=True,
                text=True,
                timeout=12,
                shell=False
            )
            output = res.stdout if res.returncode == 0 else (res.stderr or res.stdout)
            status = "completed" if res.returncode == 0 else "failed"

            result = {
                "action_id": action_id,
                "status": status,
                "output": output[:3000],  # Safe output truncation
                "returncode": res.returncode,
                "executed_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            }
            action["status"] = status
            action["result"] = result
            return result
        except subprocess.TimeoutExpired:
            logger.error(f"Action execution timed out: {action_id}")
            result = {
                "action_id": action_id,
                "status": "timed_out",
                "error": "Execution timed out after 12 seconds.",
                "executed_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            }
            action["status"] = "timed_out"
            return result
        except Exception as e:
            logger.error(f"Error executing action {action_id}: {e}")
            result = {
                "action_id": action_id,
                "status": "error",
                "error": str(e),
                "executed_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            }
            action["status"] = "error"
            return result
