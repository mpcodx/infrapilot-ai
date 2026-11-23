import uuid
import asyncio
import pytest
import asyncssh
import httpx
from contextlib import asynccontextmanager
from typing import Dict, Any

from backend.app.main import app
from backend.app.core.database import SessionLocal
from backend.app.core.encryption import encrypt_secret, decrypt_secret, mask_credential
from backend.app.models.models import ManagedServer
from backend.app.services.ssh_service import SSHService, InfraPilotSSHClient, PiOpsSSHClient


# --- Mock SSH Server Implementation ---

class MockLinuxSSHServer(asyncssh.SSHServer):
    def __init__(self, authorized_keys=None):
        self.authorized_keys = authorized_keys or []

    def password_auth_supported(self):
        return True

    def validate_password(self, username, password):
        return username == "testadmin" and password == "correct_horse_battery"

    def public_key_auth_supported(self):
        return bool(self.authorized_keys)

    def validate_public_key(self, username, key):
        if username == "keyadmin":
            for auth_key in self.authorized_keys:
                if key.get_fingerprint() == auth_key.get_fingerprint():
                    return True
        return False


def handle_process(process: asyncssh.SSHServerProcess):
    cmd = process.command or ""
    if "echo PIIOPS_OK" in cmd:
        process.stdout.write("PIIOPS_OK\n")
    elif "uname -s -r -m -n" in cmd:
        process.stdout.write("Linux srv-prod-01 6.8.0-generic x86_64\n")
    elif "cat /etc/os-release" in cmd:
        process.stdout.write('PRETTY_NAME="Ubuntu 24.04 LTS"\nVERSION_ID="24.04"\n')
    elif "cat /proc/uptime" in cmd:
        process.stdout.write("86400.50 172800.00\n")
    elif "nproc" in cmd:
        process.stdout.write("8\n")
    elif "cat /proc/loadavg" in cmd:
        process.stdout.write("0.45 0.35 0.30 2/240 5678\n")
    elif "grep -m1 'model name'" in cmd:
        process.stdout.write("model name : Intel(R) Xeon(R) Gold 6330\n")
    elif "free -b" in cmd:
        process.stdout.write("Mem: 33554432000 16777216000 16777216000 0 0 16777216000\nSwap: 8388608000 0 8388608000\n")
    elif "df -B1 -P" in cmd:
        process.stdout.write("Filesystem 1024-blocks Used Available Capacity Mounted on\n/dev/sda1 200000000000 80000000000 120000000000 40% /\n")
    elif "cat /proc/net/dev" in cmd:
        process.stdout.write("Inter-|   Receive\n face |bytes\n  eth0: 500000000 0 0 0 0 0 0 0 250000000\n")
    elif "ps -eo" in cmd:
        process.stdout.write("PID USER %CPU %MEM COMMAND\n 1 root 0.0 0.1 systemd\n 500 nginx 1.2 0.5 nginx\n 900 app 4.5 3.0 python\n")
    elif "systemctl list-units" in cmd:
        process.stdout.write("nginx.service loaded active running Nginx Web Server\nssh.service loaded active running OpenBSD Secure Shell server\n")
    elif "ss -tuln" in cmd:
        process.stdout.write("Netid State Local Address:Port\ntcp LISTEN 0.0.0.0:80\ntcp LISTEN 127.0.0.1:5432\n")
    elif "docker ps" in cmd:
        process.stdout.write("c101\tweb-proxy\tnginx:alpine\tUp 3 days\trunning\n")
    elif "cat /etc/ssh/sshd_config" in cmd:
        process.stdout.write("PermitRootLogin no\nPasswordAuthentication yes\n")
    elif "ufw status" in cmd:
        process.stdout.write("Status: active\n")
    elif "systemctl restart nginx" in cmd:
        process.stdout.write("Restarting nginx...\n")
        process.exit(0)
        return
    elif "missing_command_test" in cmd:
        process.stderr.write("bash: command not found\n")
        process.exit(127)
        return
    else:
        process.stdout.write("OK\n")

    process.exit(0)


@asynccontextmanager
async def start_mock_ssh_servers(port1=2242, port2=2243):
    key1 = asyncssh.generate_private_key("ssh-ed25519")
    fp1 = key1.get_fingerprint()

    key2 = asyncssh.generate_private_key("ssh-ed25519")
    fp2 = key2.get_fingerprint()
    client_key = asyncssh.generate_private_key("ssh-ed25519")

    s1 = await asyncssh.create_server(
        MockLinuxSSHServer,
        "127.0.0.1",
        port1,
        server_host_keys=[key1],
        process_factory=handle_process,
    )
    s2 = await asyncssh.create_server(
        lambda: MockLinuxSSHServer(authorized_keys=[client_key]),
        "127.0.0.1",
        port2,
        server_host_keys=[key2],
        process_factory=handle_process,
    )

    try:
        yield {
            "s1": {"port": port1, "fp": fp1},
            "s2": {
                "port": port2,
                "fp": fp2,
                "client_key_str": client_key.export_private_key().decode(),
                "client_key_obj": client_key,
            },
        }
    finally:
        s1.close()
        s2.close()
        await s1.wait_closed()
        await s2.wait_closed()


# --- Test Cases ---

def test_credential_encryption_and_masking():
    secret = "TopSecretSSHPassword123!"
    encrypted = encrypt_secret(secret)
    assert encrypted != secret
    assert decrypt_secret(encrypted) == secret
    assert mask_credential(secret) == "••••••••••••••••"


@pytest.mark.asyncio
async def test_ssh_password_auth_success():
    async with start_mock_ssh_servers(port1=2244, port2=2245) as ssh_servers:
        res = await SSHService.test_connection(
            hostname="127.0.0.1",
            port=ssh_servers["s1"]["port"],
            username="testadmin",
            auth_method="password",
            credential="correct_horse_battery",
        )
        assert res["success"] is True
        assert "successful" in res["message"].lower()
        assert res["host_key_fingerprint"] == ssh_servers["s1"]["fp"]


@pytest.mark.asyncio
async def test_ssh_password_auth_invalid_credentials():
    async with start_mock_ssh_servers(port1=2246, port2=2247) as ssh_servers:
        res = await SSHService.test_connection(
            hostname="127.0.0.1",
            port=ssh_servers["s1"]["port"],
            username="testadmin",
            auth_method="password",
            credential="WRONG_PASSWORD",
        )
        assert res["success"] is False
        assert "failed" in res["message"].lower() or "denied" in res["message"].lower()


@pytest.mark.asyncio
async def test_ssh_key_auth_success():
    async with start_mock_ssh_servers(port1=2248, port2=2249) as ssh_servers:
        res = await SSHService.test_connection(
            hostname="127.0.0.1",
            port=ssh_servers["s2"]["port"],
            username="keyadmin",
            auth_method="private_key",
            credential=ssh_servers["s2"]["client_key_str"],
        )
        assert res["success"] is True
        assert res["host_key_fingerprint"] == ssh_servers["s2"]["fp"]


@pytest.mark.asyncio
async def test_ssh_key_auth_invalid_key():
    async with start_mock_ssh_servers(port1=2250, port2=2251) as ssh_servers:
        other_key = asyncssh.generate_private_key("ssh-ed25519").export_private_key().decode()
        res = await SSHService.test_connection(
            hostname="127.0.0.1",
            port=ssh_servers["s2"]["port"],
            username="keyadmin",
            auth_method="private_key",
            credential=other_key,
        )
        assert res["success"] is False


@pytest.mark.asyncio
async def test_ssh_host_key_mismatch_rejected():
    async with start_mock_ssh_servers(port1=2252, port2=2253) as ssh_servers:
        fake_expected_fp = "SHA256:FAKE_UNTRUSTED_FINGERPRINT_12345"
        res = await SSHService.test_connection(
            hostname="127.0.0.1",
            port=ssh_servers["s1"]["port"],
            username="testadmin",
            auth_method="password",
            credential="correct_horse_battery",
            expected_fingerprint=fake_expected_fp,
            allow_first_trust=False,
        )
        assert res["success"] is False
        assert "mismatch" in res["message"].lower()


@pytest.mark.asyncio
async def test_ssh_connection_timeout():
    res = await SSHService.test_connection(
        hostname="192.0.2.1",
        port=22,
        username="root",
        auth_method="password",
        credential="pass",
        timeout=2,
    )
    assert res["success"] is False


@pytest.mark.asyncio
async def test_ssh_discovery_parsing():
    async with start_mock_ssh_servers(port1=2254, port2=2255) as ssh_servers:
        db = SessionLocal()
        srv_id = f"test-srv-{uuid.uuid4().hex[:8]}"
        try:
            server = ManagedServer(
                server_id=srv_id,
                name="Production Cluster 01",
                hostname="127.0.0.1",
                ssh_port=ssh_servers["s1"]["port"],
                username="testadmin",
                auth_method="password",
                encrypted_credential=encrypt_secret("correct_horse_battery"),
                timeout_seconds=5,
                is_host_key_trusted=True,
                host_key_fingerprint=ssh_servers["s1"]["fp"],
                status="online",
            )
            db.add(server)
            db.commit()

            data = await SSHService.discover_server(server)

            assert data["hostname"] == "srv-prod-01"
            assert data["os_name"] == "Ubuntu 24.04 LTS"
            assert data["kernel_version"] == "6.8.0-generic"
            assert data["architecture"] == "x86_64"
            assert data["cpu_count"] == 8
            assert data["cpu_model"] == "Intel(R) Xeon(R) Gold 6330"
            assert data["ram_total"] == 33554432000
            assert data["disk_total"] == 200000000000
            assert len(data["processes"]) >= 2
            assert any(p["name"] == "nginx" for p in data["processes"])
            assert len(data["services"]) >= 1
            assert any(s["name"] == "nginx.service" for s in data["services"])
            assert len(data["containers"]) >= 1
            assert data["containers"][0]["name"] == "web-proxy"
        finally:
            db.query(ManagedServer).filter(ManagedServer.server_id == srv_id).delete()
            db.commit()
            db.close()


def test_ssh_client_alias():
    assert PiOpsSSHClient is InfraPilotSSHClient


@pytest.mark.asyncio
async def test_ssh_missing_remote_commands_handled():
    async with start_mock_ssh_servers(port1=2256, port2=2257) as ssh_servers:
        client = InfraPilotSSHClient(allow_first_trust=True)
        conn = await asyncssh.connect(
            host="127.0.0.1",
            port=ssh_servers["s1"]["port"],
            username="testadmin",
            password="correct_horse_battery",
            client_factory=lambda: client,
            known_hosts=(),
        )
        async with conn:
            out = await SSHService.run_safe_command(conn, "missing_command_test 2>/dev/null || true")
            assert out == ""


@pytest.mark.asyncio
async def test_servers_api_lifecycle():
    async with start_mock_ssh_servers(port1=2258, port2=2259) as ssh_servers:
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
            # 1. Test Ad-hoc connection
            test_res = await ac.post("/api/v1/servers/test", json={
                "hostname": "127.0.0.1",
                "ssh_port": ssh_servers["s1"]["port"],
                "username": "testadmin",
                "auth_method": "password",
                "credential": "correct_horse_battery",
                "timeout_seconds": 5,
            })
            assert test_res.status_code == 200
            assert test_res.json()["success"] is True

            # 2. Create server
            create_res = await ac.post("/api/v1/servers", json={
                "name": "Live Mock Node 01",
                "hostname": "127.0.0.1",
                "ssh_port": ssh_servers["s1"]["port"],
                "username": "testadmin",
                "auth_method": "password",
                "credential": "correct_horse_battery",
                "auto_trust_host_key": True,
                "environment": "production",
                "tags": ["prod", "web"],
            })
            assert create_res.status_code == 201
            server_data = create_res.json()
            server_id = server_data["server_id"]
            assert server_data["has_credential"] is True
            assert "credential" not in server_data

            # 3. Retrieve server
            get_res = await ac.get(f"/api/v1/servers/{server_id}")
            assert get_res.status_code == 200
            assert get_res.json()["name"] == "Live Mock Node 01"

            # 4. Trigger Discovery via API
            disc_res = await ac.post(f"/api/v1/servers/{server_id}/discover")
            assert disc_res.status_code == 200
            assert disc_res.json()["data"]["hostname"] == "srv-prod-01"

            # 5. Remote Action Preview & Approval
            prev_res = await ac.post(f"/api/v1/servers/{server_id}/action/preview", json={
                "action_type": "restart_service",
                "target": "nginx",
            })
            assert prev_res.status_code == 200
            action_token = prev_res.json()["action_id"]

            # Command injection attempt on target must be rejected
            bad_prev = await ac.post(f"/api/v1/servers/{server_id}/action/preview", json={
                "action_type": "restart_service",
                "target": "nginx; rm -rf /",
            })
            assert bad_prev.status_code == 400

            # Approve and execute
            app_res = await ac.post(f"/api/v1/servers/{server_id}/action/approve", json={
                "action_id": action_token,
                "confirmed": True,
            })
            assert app_res.status_code == 200
            assert app_res.json()["status"] == "completed"

            # 6. Delete server and revoke credentials
            del_res = await ac.delete(f"/api/v1/servers/{server_id}")
            assert del_res.status_code == 200
            assert (await ac.get(f"/api/v1/servers/{server_id}")).status_code == 404


@pytest.mark.asyncio
async def test_ai_multi_server_telemetry_analysis():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post("/api/v1/ai/chat", json={
            "message": "Which server has the highest CPU usage?",
            "all_servers": True,
            "include_system_context": False,
        })
        assert res.status_code == 200
        data = res.json()
        assert "response" in data
        assert len(data["response"]) > 0
