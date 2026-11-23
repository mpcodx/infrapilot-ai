import subprocess
import shutil
import psutil
from typing import List, Dict, Any, Optional

try:
    import docker
except ImportError:
    docker = None


class DiscoveryService:
    @staticmethod
    def get_processes(limit: int = 50) -> List[Dict[str, Any]]:
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'memory_info', 'status', 'username', 'cmdline']):
            try:
                info = proc.info
                mem_rss = info['memory_info'].rss if info.get('memory_info') else 0
                cmdline = " ".join(info.get('cmdline') or []) if info.get('cmdline') else ""
                processes.append({
                    "pid": info['pid'],
                    "name": info['name'] or "unknown",
                    "cpu_percent": float(info.get('cpu_percent') or 0.0),
                    "memory_percent": float(info.get('memory_percent') or 0.0),
                    "memory_rss": int(mem_rss),
                    "status": info.get('status') or "unknown",
                    "username": info.get('username') or "unknown",
                    "cmdline": cmdline[:250],
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

        processes.sort(key=lambda x: (x["cpu_percent"] + x["memory_percent"]), reverse=True)
        return processes[:limit]

    @staticmethod
    def get_ports() -> List[Dict[str, Any]]:
        ports = []
        try:
            connections = psutil.net_connections(kind="inet")
            for conn in connections:
                if conn.status == "LISTEN" or conn.type == 2:  # 2 is SOCK_DGRAM (UDP)
                    proto = "tcp" if conn.type == 1 else "udp"
                    proc_name = None
                    if conn.pid:
                        try:
                            proc = psutil.Process(conn.pid)
                            proc_name = proc.name()
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            proc_name = "restricted"

                    laddr = conn.laddr
                    ports.append({
                        "protocol": proto,
                        "local_address": laddr.ip if hasattr(laddr, 'ip') else str(laddr),
                        "local_port": laddr.port if hasattr(laddr, 'port') else 0,
                        "status": conn.status or "OPEN",
                        "pid": conn.pid,
                        "process_name": proc_name,
                    })
        except (psutil.AccessDenied, Exception):
            # Fallback to ss command if psutil net_connections permission is restricted
            if shutil.which("ss"):
                try:
                    res = subprocess.run(["ss", "-tulnp"], capture_output=True, text=True, timeout=2)
                    lines = res.stdout.strip().split("\n")[1:]
                    for line in lines:
                        parts = line.split()
                        if len(parts) >= 5:
                            proto = parts[0].lower()
                            state = parts[1]
                            local = parts[4]
                            if ":" in local:
                                host, port_str = local.rsplit(":", 1)
                                try:
                                    port = int(port_str)
                                    proc_name = parts[6] if len(parts) > 6 else None
                                    ports.append({
                                        "protocol": proto,
                                        "local_address": host,
                                        "local_port": port,
                                        "status": state,
                                        "pid": None,
                                        "process_name": proc_name,
                                    })
                                except ValueError:
                                    continue
                except Exception:
                    pass

        # Deduplicate
        seen = set()
        deduped = []
        for p in ports:
            key = (p["protocol"], p["local_address"], p["local_port"])
            if key not in seen:
                seen.add(key)
                deduped.append(p)

        deduped.sort(key=lambda x: x["local_port"])
        return deduped

    @staticmethod
    def get_services() -> List[Dict[str, Any]]:
        services = []
        if shutil.which("systemctl"):
            try:
                cmd = ["systemctl", "list-units", "--type=service", "--all", "--no-pager", "--no-legend"]
                res = subprocess.run(cmd, capture_output=True, text=True, timeout=3)
                if res.returncode == 0:
                    for line in res.stdout.strip().split("\n"):
                        if not line:
                            continue
                        parts = line.split(None, 4)
                        if len(parts) >= 4:
                            name = parts[0].replace(".service", "")
                            load = parts[1]
                            active = parts[2]
                            sub = parts[3]
                            desc = parts[4] if len(parts) > 4 else ""
                            services.append({
                                "name": name,
                                "load_state": load,
                                "active_state": active,
                                "sub_state": sub,
                                "description": desc,
                                "is_active": (active == "active"),
                                "ports": [],
                            })
            except Exception:
                pass

        if not services:
            # Fallback for systems where systemctl is not available (e.g. basic containers or init)
            for proc in psutil.process_iter(['name']):
                try:
                    name = proc.info['name']
                    if name and name not in [s["name"] for s in services]:
                        services.append({
                            "name": name,
                            "load_state": "loaded",
                            "active_state": "active",
                            "sub_state": "running",
                            "description": f"Process daemon {name}",
                            "is_active": True,
                            "ports": [],
                        })
                except Exception:
                    continue

        return services[:100]

    @staticmethod
    def get_containers() -> List[Dict[str, Any]]:
        containers = []
        if not docker:
            return containers

        try:
            client = docker.from_env(timeout=2)
            raw_containers = client.containers.list(all=True)
            for c in raw_containers:
                ports = {}
                if c.attrs.get("NetworkSettings", {}).get("Ports"):
                    ports = c.attrs["NetworkSettings"]["Ports"]

                state = c.attrs.get("State", {})
                health_info = state.get("Health", {}).get("Status", "none")
                restart_count = c.attrs.get("RestartCount", 0)

                containers.append({
                    "id": c.short_id,
                    "name": c.name.lstrip("/"),
                    "image": c.image.tags[0] if c.image.tags else c.image.short_id,
                    "status": c.status,
                    "state": state.get("Status", c.status),
                    "health": health_info,
                    "restart_count": restart_count,
                    "cpu_percent": 0.0,
                    "memory_usage": 0,
                    "memory_limit": 0,
                    "ports": ports,
                })
        except Exception:
            # Docker daemon not accessible or not running - handled gracefully
            pass

        return containers
