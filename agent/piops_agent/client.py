import time
import socket
import platform
import logging
import requests
import psutil
from typing import Dict, Any, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("infrapilot-agent")


class InfraPilotAgent:
    def __init__(self, backend_url: str, shared_secret: str, interval: int = 10):
        self.backend_url = backend_url.rstrip("/")
        self.shared_secret = shared_secret
        self.interval = interval
        self.agent_id: Optional[str] = None
        self.auth_token: Optional[str] = None
        self.running = False

    def collect_metrics(self) -> Dict[str, Any]:
        """Collect restricted system metrics without requiring root access."""
        cpu_pct = psutil.cpu_percent(interval=0.1)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage("/")

        return {
            "hostname": platform.node(),
            "cpu_percent": float(cpu_pct),
            "ram_percent": float(mem.percent),
            "ram_available_mb": round(mem.available / (1024 * 1024), 2),
            "disk_percent": float(disk.percent),
            "uptime_seconds": round(time.time() - psutil.boot_time(), 1),
        }

    def register(self) -> bool:
        """Register agent with the central control center."""
        reg_url = f"{self.backend_url}/api/v1/agents/register"
        payload = {
            "hostname": platform.node(),
            "os_info": f"{platform.system()} {platform.release()}",
            "ip_address": socket.gethostbyname(socket.gethostname()),
            "capabilities": ["metrics", "health"],
            "shared_secret": self.shared_secret,
        }

        try:
            res = requests.post(reg_url, json=payload, timeout=5)
            if res.status_code == 200:
                data = res.json()
                self.agent_id = data.get("agent_id")
                self.auth_token = data.get("token")
                logger.info(f"Agent successfully registered. ID: {self.agent_id}")
                return True
            else:
                logger.error(f"Registration rejected by server: {res.status_code} - {res.text}")
                return False
        except Exception as e:
            logger.error(f"Registration connection failed: {e}")
            return False

    def send_heartbeat(self) -> bool:
        """Send authenticated heartbeat with collected metrics."""
        if not self.agent_id or not self.auth_token:
            logger.warning("Agent not registered yet.")
            return False

        url = f"{self.backend_url}/api/v1/agents/heartbeat"
        metrics = self.collect_metrics()
        payload = {
            "agent_id": self.agent_id,
            "token": self.auth_token,
            "metrics": metrics,
        }

        try:
            res = requests.post(url, json=payload, timeout=5)
            return res.status_code == 200
        except Exception as e:
            logger.error(f"Failed to deliver heartbeat: {e}")
            return False

    def run_once(self) -> bool:
        """Run single registration and heartbeat cycle."""
        if not self.agent_id:
            if not self.register():
                return False
        return self.send_heartbeat()


# Backward-compatible alias
PIopsAgent = InfraPilotAgent


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="InfraPilot AI Standalone Monitoring Agent")
    parser.add_argument("--url", default="http://127.0.0.1:8000", help="InfraPilot AI backend URL")
    parser.add_argument("--secret", default="dev-agent-secret-key-change-for-production", help="Shared secret")
    parser.add_argument("--interval", type=int, default=10, help="Heartbeat interval in seconds")
    args = parser.parse_args()

    agent = InfraPilotAgent(backend_url=args.url, shared_secret=args.secret, interval=args.interval)
    logger.info("Starting InfraPilot Linux Agent...")
    if agent.register():
        try:
            while True:
                agent.send_heartbeat()
                time.sleep(args.interval)
        except KeyboardInterrupt:
            logger.info("Agent stopped by operator.")
