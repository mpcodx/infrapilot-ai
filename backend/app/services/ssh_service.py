import asyncio
import re
import time
import logging
from typing import Dict, Any, Optional, Tuple, List
import asyncssh
from backend.app.core.encryption import decrypt_secret

logger = logging.getLogger("infrapilot-ssh")


class HostKeyVerificationNeeded(Exception):
    def __init__(self, fingerprint: str, key_type: str, message: str = "Host key requires explicit operator trust"):
        super().__init__(message)
        self.fingerprint = fingerprint
        self.key_type = key_type


class MismatchedHostKeyError(Exception):
    pass


class InfraPilotSSHClient(asyncssh.SSHClient):
    """Custom SSH client to handle fingerprint capture and verification."""
    def __init__(self, expected_fingerprint: Optional[str] = None, allow_first_trust: bool = False):
        super().__init__()
        self.expected_fingerprint = expected_fingerprint
        self.allow_first_trust = allow_first_trust
        self.observed_fingerprint: Optional[str] = None
        self.observed_key_type: Optional[str] = None

    def validate_host_public_key(self, host: str, addr: str, port: int, key: asyncssh.SSHKey) -> bool:
        # Extract SHA256 fingerprint in standard format (e.g. SHA256:abc...)
        raw_fp = key.get_fingerprint()
        self.observed_fingerprint = raw_fp
        self.observed_key_type = key.get_algorithm()

        # If we have an expected, trusted fingerprint, it MUST match
        if self.expected_fingerprint:
            if self.observed_fingerprint != self.expected_fingerprint:
                raise MismatchedHostKeyError(
                    f"Host key mismatch for {host}:{port}! "
                    f"Expected {self.expected_fingerprint}, got {self.observed_fingerprint}. "
                    "Connection aborted to protect against potential Man-in-the-Middle attack."
                )
            return True

        # If no expected fingerprint, check if first trust is allowed
        if self.allow_first_trust:
            return True

        # Otherwise require explicit confirmation
        raise HostKeyVerificationNeeded(
            fingerprint=self.observed_fingerprint,
            key_type=self.observed_key_type,
            message=f"Untrusted host key for {host}:{port}. Fingerprint: {self.observed_fingerprint}"
        )


# Backward-compatible alias
PiOpsSSHClient = InfraPilotSSHClient


class SSHService:
    """Enterprise SSH connection and discovery engine for remote Linux servers."""

    @staticmethod
    async def test_connection(
        hostname: str,
        port: int = 22,
        username: str = "root",
        auth_method: str = "password",
        credential: Optional[str] = None,
        passphrase: Optional[str] = None,
        timeout: int = 10,
        expected_fingerprint: Optional[str] = None,
        allow_first_trust: bool = True,
    ) -> Dict[str, Any]:
        """Test SSH connectivity and return host key details and latency."""
        start_time = time.time()
        client = InfraPilotSSHClient(expected_fingerprint=expected_fingerprint, allow_first_trust=allow_first_trust)

        connect_kwargs: Dict[str, Any] = {
            "host": hostname,
            "port": port,
            "username": username,
            "client_factory": lambda: client,
            "known_hosts": (),  # Bypasses local file and triggers validate_host_public_key
            "connect_timeout": timeout,
            "login_timeout": timeout,
        }

        if auth_method == "password":
            connect_kwargs["password"] = credential or ""
        elif auth_method == "private_key":
            if not credential:
                return {"success": False, "message": "Private key credential is required for key auth"}
            try:
                client_key = asyncssh.import_private_key(credential, passphrase=passphrase)
                connect_kwargs["client_keys"] = [client_key]
            except Exception as e:
                return {"success": False, "message": f"Failed to parse private key: {str(e)}"}

        try:
            async with asyncssh.connect(**connect_kwargs) as conn:
                # Run quick echo check
                res = await conn.run("echo PIIOPS_OK", timeout=timeout)
                latency = round((time.time() - start_time) * 1000, 2)
                return {
                    "success": True,
                    "message": "SSH authentication successful",
                    "host_key_fingerprint": client.observed_fingerprint,
                    "host_key_type": client.observed_key_type,
                    "is_host_key_trusted": True,
                    "latency_ms": latency,
                    "details": {"echo": res.stdout.strip()},
                }
        except HostKeyVerificationNeeded as e:
            latency = round((time.time() - start_time) * 1000, 2)
            return {
                "success": False,
                "message": "Host key verification needed",
                "host_key_fingerprint": e.fingerprint,
                "host_key_type": e.key_type,
                "is_host_key_trusted": False,
                "latency_ms": latency,
            }
        except MismatchedHostKeyError as e:
            return {
                "success": False,
                "message": str(e),
                "host_key_fingerprint": client.observed_fingerprint,
                "host_key_type": client.observed_key_type,
                "is_host_key_trusted": False,
            }
        except asyncssh.PermissionDenied:
            return {"success": False, "message": "SSH authentication failed (Permission denied)"}
        except (asyncio.TimeoutError, asyncssh.TimeoutError):
            return {"success": False, "message": f"Connection timed out after {timeout} seconds"}
        except Exception as e:
            return {"success": False, "message": f"SSH connection error: {str(e)}"}

    @classmethod
    async def get_connection(cls, server: Any) -> Tuple[asyncssh.SSHClientConnection, InfraPilotSSHClient]:
        """Establish a verified connection using decrypted credentials from ManagedServer."""
        password = None
        client_keys = None

        if server.auth_method == "password" and server.encrypted_credential:
            password = decrypt_secret(server.encrypted_credential)
        elif server.auth_method == "private_key" and server.encrypted_credential:
            raw_key = decrypt_secret(server.encrypted_credential)
            passphrase = decrypt_secret(server.encrypted_passphrase) if server.encrypted_passphrase else None
            client_keys = [asyncssh.import_private_key(raw_key, passphrase=passphrase)]

        expected_fp = server.host_key_fingerprint if server.is_host_key_trusted else None
        client = InfraPilotSSHClient(expected_fingerprint=expected_fp, allow_first_trust=server.is_host_key_trusted)

        conn = await asyncssh.connect(
            host=server.hostname,
            port=server.ssh_port,
            username=server.username,
            password=password,
            client_keys=client_keys,
            client_factory=lambda: client,
            known_hosts=(),
            connect_timeout=server.timeout_seconds,
            login_timeout=server.timeout_seconds,
        )
        return conn, client

    @classmethod
    async def run_safe_command(cls, conn: asyncssh.SSHClientConnection, cmd: str, timeout: int = 15) -> str:
        """Run a single read-only diagnostic command with bounded execution."""
        try:
            res = await conn.run(cmd, timeout=timeout)
            return res.stdout or ""
        except Exception as e:
            logger.warning(f"Command '{cmd}' failed or timed out: {e}")
            return ""

    @classmethod
    async def discover_server(cls, server: Any) -> Dict[str, Any]:
        """Perform comprehensive, read-only discovery on a remote Linux server via SSH."""
        conn, client = await cls.get_connection(server)
        async with conn:
            # 1. OS & Kernel Info
            uname_raw = await cls.run_safe_command(conn, "uname -s -r -m -n")
            os_release_raw = await cls.run_safe_command(conn, "cat /etc/os-release 2>/dev/null")
            uptime_raw = await cls.run_safe_command(conn, "cat /proc/uptime 2>/dev/null")

            os_name = "Linux"
            os_version = ""
            for line in os_release_raw.splitlines():
                if line.startswith("PRETTY_NAME="):
                    os_name = line.split("=", 1)[1].strip('"\'')
                elif line.startswith("VERSION_ID="):
                    os_version = line.split("=", 1)[1].strip('"\'')

            uname_parts = uname_raw.strip().split()
            hostname = uname_parts[1] if len(uname_parts) > 1 else server.hostname
            kernel_version = uname_parts[2] if len(uname_parts) > 2 else ""
            architecture = uname_parts[3] if len(uname_parts) > 3 else "x86_64"

            uptime_seconds = 0.0
            if uptime_raw.strip():
                try:
                    uptime_seconds = float(uptime_raw.strip().split()[0])
                except Exception:
                    pass

            # 2. CPU Specs & Load
            nproc_raw = await cls.run_safe_command(conn, "nproc 2>/dev/null || grep -c ^processor /proc/cpuinfo")
            cpu_model_raw = await cls.run_safe_command(conn, "grep -m1 'model name' /proc/cpuinfo 2>/dev/null")
            cpu_count = int(nproc_raw.strip()) if nproc_raw.strip().isdigit() else 1
            cpu_model = cpu_model_raw.split(":", 1)[1].strip() if ":" in cpu_model_raw else "Linux Processor"

            loadavg_raw = await cls.run_safe_command(conn, "cat /proc/loadavg 2>/dev/null")
            load_avg = [0.0, 0.0, 0.0]
            if loadavg_raw.strip():
                try:
                    parts = loadavg_raw.strip().split()
                    load_avg = [float(parts[0]), float(parts[1]), float(parts[2])]
                except Exception:
                    pass

            # Calculate approx CPU utilization from load average vs cores
            cpu_percent = min(100.0, round((load_avg[0] / max(1, cpu_count)) * 100, 1))

            # 3. Memory & Swap
            free_raw = await cls.run_safe_command(conn, "free -b 2>/dev/null")
            ram_total = 0
            ram_used = 0
            ram_available = 0
            swap_total = 0
            swap_used = 0

            for line in free_raw.splitlines():
                parts = line.split()
                if not parts:
                    continue
                if parts[0].startswith("Mem:"):
                    ram_total = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
                    ram_used = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 0
                    ram_available = int(parts[6]) if len(parts) > 6 and parts[6].isdigit() else (ram_total - ram_used)
                elif parts[0].startswith("Swap:"):
                    swap_total = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
                    swap_used = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 0

            ram_percent = round((ram_used / ram_total) * 100, 1) if ram_total > 0 else 0.0
            swap_percent = round((swap_used / swap_total) * 100, 1) if swap_total > 0 else 0.0

            # 4. Storage & Filesystem
            df_raw = await cls.run_safe_command(conn, "df -B1 -P 2>/dev/null")
            disk_total = 0
            disk_used = 0
            disk_free = 0
            partitions = []

            for line in df_raw.splitlines()[1:]:
                parts = line.split()
                if len(parts) >= 6:
                    try:
                        size = int(parts[1])
                        used = int(parts[2])
                        avail = int(parts[3])
                        mount = parts[5]
                        partitions.append({
                            "device": parts[0],
                            "mountpoint": mount,
                            "total": size,
                            "used": used,
                            "free": avail,
                            "percent": float(parts[4].replace("%", "")),
                        })
                        if mount == "/":
                            disk_total = size
                            disk_used = used
                            disk_free = avail
                    except Exception:
                        pass

            disk_percent = round((disk_used / disk_total) * 100, 1) if disk_total > 0 else 0.0

            # 5. Network Interfaces
            net_raw = await cls.run_safe_command(conn, "cat /proc/net/dev 2>/dev/null")
            net_bytes_recv = 0
            net_bytes_sent = 0
            interfaces = []
            for line in net_raw.splitlines()[2:]:
                if ":" in line:
                    iface, stats = line.split(":", 1)
                    iface = iface.strip()
                    s = stats.split()
                    if len(s) >= 9:
                        try:
                            rx = int(s[0])
                            tx = int(s[8])
                            net_bytes_recv += rx
                            net_bytes_sent += tx
                            interfaces.append({"interface": iface, "bytes_recv": rx, "bytes_sent": tx})
                        except Exception:
                            pass

            # 6. Running Processes (Top 25)
            ps_raw = await cls.run_safe_command(conn, "ps -eo pid,user,%cpu,%mem,comm --sort=-%cpu 2>/dev/null | head -n 26")
            processes = []
            for line in ps_raw.splitlines()[1:]:
                parts = line.split(None, 4)
                if len(parts) >= 5:
                    try:
                        processes.append({
                            "pid": int(parts[0]),
                            "username": parts[1],
                            "cpu_percent": float(parts[2]),
                            "memory_percent": float(parts[3]),
                            "name": parts[4].strip(),
                        })
                    except Exception:
                        pass

            # 7. Systemd Services
            services_raw = await cls.run_safe_command(
                conn, "systemctl list-units --type=service --all --no-pager --no-legend 2>/dev/null | head -n 40"
            )
            services = []
            for line in services_raw.splitlines():
                parts = line.split(None, 4)
                if len(parts) >= 4:
                    services.append({
                        "name": parts[0],
                        "load_state": parts[1],
                        "active_state": parts[2],
                        "sub_state": parts[3],
                        "description": parts[4] if len(parts) > 4 else "",
                        "is_active": (parts[2] == "active"),
                    })

            # 8. Listening Ports
            ports_raw = await cls.run_safe_command(conn, "ss -tuln 2>/dev/null || netstat -tuln 2>/dev/null")
            ports = []
            for line in ports_raw.splitlines():
                parts = line.split()
                if len(parts) >= 5 and (parts[0] in ("tcp", "udp", "LISTEN", "UNCONN")):
                    proto = parts[0].lower()
                    local_addr = parts[4] if "LISTEN" in line or "UNCONN" in line else parts[3]
                    if ":" in local_addr:
                        ip_p, port_p = local_addr.rsplit(":", 1)
                        if port_p.isdigit():
                            ports.append({"proto": proto, "ip": ip_p, "port": int(port_p)})

            # 9. Docker Availability & Containers
            docker_raw = await cls.run_safe_command(
                conn, "docker ps -a --format '{{.ID}}\t{{.Names}}\t{{.Image}}\t{{.Status}}\t{{.State}}' 2>/dev/null || true"
            )
            containers = []
            for line in docker_raw.splitlines():
                parts = line.split("\t")
                if len(parts) >= 4:
                    containers.append({
                        "container_id": parts[0],
                        "name": parts[1],
                        "image": parts[2],
                        "status": parts[3],
                        "state": parts[4] if len(parts) > 4 else "running",
                    })

            # 10. Defensive Security Checks
            security_findings = []
            # Check SSH root login and password config
            ssh_conf_raw = await cls.run_safe_command(
                conn, "cat /etc/ssh/sshd_config 2>/dev/null || cat /etc/ssh/sshd_config.d/*.conf 2>/dev/null"
            )
            if "PermitRootLogin yes" in ssh_conf_raw:
                security_findings.append({
                    "finding_id": f"ssh_root_login_{server.server_id}",
                    "severity": "high",
                    "category": "ssh",
                    "title": "SSH Root Login Permitted",
                    "description": "Remote SSH configuration allows root user login with password.",
                    "affected_component": "sshd_config",
                    "evidence": "PermitRootLogin yes found in SSH configuration",
                    "recommended_fix": "Set 'PermitRootLogin no' or 'PermitRootLogin prohibit-password' in /etc/ssh/sshd_config",
                })

            # Check public listening database ports
            for p in ports:
                if p["port"] in (5432, 3306, 6379, 27017) and p["ip"] in ("0.0.0.0", "::", "*"):
                    security_findings.append({
                        "finding_id": f"public_db_{p['port']}_{server.server_id}",
                        "severity": "high",
                        "category": "network",
                        "title": f"Database Port {p['port']} Publicly Exposed",
                        "description": f"Service on port {p['port']} is bound to 0.0.0.0 without localhost isolation.",
                        "affected_component": f"Port {p['port']}",
                        "evidence": f"Bound to {p['ip']}:{p['port']}",
                        "recommended_fix": "Bind database service strictly to 127.0.0.1 or configure UFW firewall.",
                    })

            # Check firewall status
            ufw_raw = await cls.run_safe_command(conn, "ufw status 2>/dev/null || true")
            if "inactive" in ufw_raw.lower():
                security_findings.append({
                    "finding_id": f"ufw_inactive_{server.server_id}",
                    "severity": "medium",
                    "category": "firewall",
                    "title": "UFW Host Firewall Inactive",
                    "description": "Uncomplicated Firewall is disabled on this remote host.",
                    "affected_component": "ufw",
                    "evidence": "ufw status returned inactive",
                    "recommended_fix": "Enable firewall with 'sudo ufw enable' and allow required ports.",
                })

            # Check shadow file permissions
            shadow_raw = await cls.run_safe_command(conn, "ls -l /etc/shadow 2>/dev/null || true")
            if shadow_raw and any(shadow_raw.startswith(p) for p in ("-rw-rw-rw-", "-rwxrwxrwx", "-rw-r--r--")):
                security_findings.append({
                    "finding_id": f"shadow_perm_{server.server_id}",
                    "severity": "critical",
                    "category": "permissions",
                    "title": "Insecure /etc/shadow Permissions",
                    "description": "/etc/shadow is world-readable or writable.",
                    "affected_component": "/etc/shadow",
                    "evidence": shadow_raw.strip(),
                    "recommended_fix": "Execute 'chmod 0640 /etc/shadow' immediately.",
                })

            return {
                "server_id": server.server_id,
                "hostname": hostname,
                "os_name": os_name,
                "os_version": os_version,
                "kernel_version": kernel_version,
                "architecture": architecture,
                "cpu_model": cpu_model,
                "cpu_count": cpu_count,
                "cpu_percent": cpu_percent,
                "ram_total": ram_total,
                "ram_used": ram_used,
                "ram_available": ram_available,
                "ram_percent": ram_percent,
                "swap_total": swap_total,
                "swap_used": swap_used,
                "swap_percent": swap_percent,
                "disk_total": disk_total,
                "disk_used": disk_used,
                "disk_free": disk_free,
                "disk_percent": disk_percent,
                "partitions": partitions,
                "uptime_seconds": uptime_seconds,
                "load_avg": load_avg,
                "net_bytes_sent": net_bytes_sent,
                "net_bytes_recv": net_bytes_recv,
                "interfaces": interfaces,
                "processes": processes,
                "services": services,
                "ports": ports,
                "containers": containers,
                "security_findings": security_findings,
            }

    @classmethod
    async def execute_approved_remote_action(
        cls, server: Any, action_type: str, target: str
    ) -> Dict[str, Any]:
        """Execute a predefined, validated remote remediation action over SSH."""
        # Enforce strict regex validation on target
        if not re.match(r"^[a-zA-Z0-9_\-\.@]{1,64}$", target):
            raise ValueError(f"Invalid target parameter: '{target}'. Target must match ^[a-zA-Z0-9_\\-\\.\\@]{{1,64}}$")

        # Map strictly to pre-compiled command templates
        templates = {
            "restart_service": f"systemctl restart {target}",
            "stop_service": f"systemctl stop {target}",
            "start_service": f"systemctl start {target}",
            "restart_container": f"docker restart {target}",
            "stop_container": f"docker stop {target}",
            "container_logs": f"docker logs --tail 100 {target}",
            "clean_docker_images": "docker image prune -f",
        }

        if action_type not in templates:
            raise ValueError(f"Action '{action_type}' is not an authorized remote action template.")

        cmd = templates[action_type]
        logger.info(f"Executing approved remote action '{action_type}' on server {server.hostname}: {cmd}")

        conn, client = await cls.get_connection(server)
        async with conn:
            res = await conn.run(cmd, timeout=30)
            return {
                "exit_status": res.exit_status,
                "stdout": (res.stdout or "")[:65536],
                "stderr": (res.stderr or "")[:65536],
                "success": (res.exit_status == 0),
            }
