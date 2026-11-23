import os
import platform
import time
import datetime
import psutil
from typing import Dict, Any, List, Optional


class LinuxCollector:
    _last_net_io: Optional[Any] = None
    _last_net_time: Optional[float] = None
    _last_disk_io: Optional[Any] = None
    _last_disk_time: Optional[float] = None

    @classmethod
    def get_cpu_info(cls) -> Dict[str, Any]:
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            cpu_count = psutil.cpu_count(logical=True) or 1
            per_cpu = psutil.cpu_percent(interval=None, percpu=True)
            freq = psutil.cpu_freq()
            freq_current = freq.current if freq else None

            return {
                "cpu_percent": float(cpu_percent),
                "cpu_count": int(cpu_count),
                "cpu_freq_current": float(freq_current) if freq_current else None,
                "per_cpu_percent": [float(p) for p in per_cpu],
            }
        except Exception as e:
            return {
                "cpu_percent": 0.0,
                "cpu_count": 1,
                "cpu_freq_current": None,
                "per_cpu_percent": [],
                "error": str(e),
            }

    @classmethod
    def get_memory_info(cls) -> Dict[str, Any]:
        try:
            mem = psutil.virtual_memory()
            swap = psutil.swap_memory()

            return {
                "ram_total": int(mem.total),
                "ram_used": int(mem.used),
                "ram_available": int(mem.available),
                "ram_percent": float(mem.percent),
                "swap_total": int(swap.total),
                "swap_used": int(swap.used),
                "swap_percent": float(swap.percent),
            }
        except Exception as e:
            return {
                "ram_total": 0,
                "ram_used": 0,
                "ram_available": 0,
                "ram_percent": 0.0,
                "swap_total": 0,
                "swap_used": 0,
                "swap_percent": 0.0,
                "error": str(e),
            }

    @classmethod
    def get_disk_info(cls) -> Dict[str, Any]:
        try:
            usage = psutil.disk_usage("/")
            now = time.time()
            io_counters = psutil.disk_io_counters()

            read_bytes_sec = 0.0
            write_bytes_sec = 0.0
            if cls._last_disk_io and cls._last_disk_time and io_counters:
                dt = max(now - cls._last_disk_time, 0.001)
                read_bytes_sec = (io_counters.read_bytes - cls._last_disk_io.read_bytes) / dt
                write_bytes_sec = (io_counters.write_bytes - cls._last_disk_io.write_bytes) / dt

            cls._last_disk_io = io_counters
            cls._last_disk_time = now

            partitions = []
            for part in psutil.disk_partitions(all=False):
                try:
                    p_usage = psutil.disk_usage(part.mountpoint)
                    partitions.append({
                        "device": part.device,
                        "mountpoint": part.mountpoint,
                        "fstype": part.fstype,
                        "total": p_usage.total,
                        "used": p_usage.used,
                        "free": p_usage.free,
                        "percent": p_usage.percent,
                    })
                except PermissionError:
                    continue

            return {
                "disk_total": int(usage.total),
                "disk_used": int(usage.used),
                "disk_free": int(usage.free),
                "disk_percent": float(usage.percent),
                "read_bytes_sec": max(0.0, float(read_bytes_sec)),
                "write_bytes_sec": max(0.0, float(write_bytes_sec)),
                "partitions": partitions,
            }
        except Exception as e:
            return {
                "disk_total": 0,
                "disk_used": 0,
                "disk_free": 0,
                "disk_percent": 0.0,
                "read_bytes_sec": 0.0,
                "write_bytes_sec": 0.0,
                "partitions": [],
                "error": str(e),
            }

    @classmethod
    def get_network_info(cls) -> Dict[str, Any]:
        try:
            now = time.time()
            net_io = psutil.net_io_counters()
            upload_bps = 0.0
            download_bps = 0.0

            if cls._last_net_io and cls._last_net_time and net_io:
                dt = max(now - cls._last_net_time, 0.001)
                upload_bps = (net_io.bytes_sent - cls._last_net_io.bytes_sent) / dt
                download_bps = (net_io.bytes_recv - cls._last_net_io.bytes_recv) / dt

            cls._last_net_io = net_io
            cls._last_net_time = now

            interfaces = {}
            for if_name, if_stats in psutil.net_if_stats().items():
                interfaces[if_name] = {
                    "isup": if_stats.isup,
                    "speed": if_stats.speed,
                    "mtu": if_stats.mtu,
                }

            return {
                "net_bytes_sent": int(net_io.bytes_sent) if net_io else 0,
                "net_bytes_recv": int(net_io.bytes_recv) if net_io else 0,
                "upload_rate_bps": max(0.0, float(upload_bps)),
                "download_rate_bps": max(0.0, float(download_bps)),
                "interfaces": interfaces,
            }
        except Exception as e:
            return {
                "net_bytes_sent": 0,
                "net_bytes_recv": 0,
                "upload_rate_bps": 0.0,
                "download_rate_bps": 0.0,
                "interfaces": {},
                "error": str(e),
            }

    @classmethod
    def get_system_summary(cls) -> Dict[str, Any]:
        try:
            hostname = platform.node()
            kernel = platform.release()
            boot_time = psutil.boot_time()
            uptime = max(0.0, time.time() - boot_time)

            os_name = "Linux"
            if os.path.exists("/etc/os-release"):
                with open("/etc/os-release", "r") as f:
                    for line in f:
                        if line.startswith("PRETTY_NAME="):
                            os_name = line.strip().split("=", 1)[1].strip('"')
                            break

            try:
                load_avg = [float(x) for x in os.getloadavg()]
            except (AttributeError, OSError):
                load_avg = [0.0, 0.0, 0.0]

            proc_count = len(psutil.pids())

            return {
                "hostname": hostname,
                "os_name": os_name,
                "kernel_version": kernel,
                "uptime_seconds": float(uptime),
                "boot_time": float(boot_time),
                "load_avg": load_avg,
                "process_count": proc_count,
            }
        except Exception as e:
            return {
                "hostname": "unknown",
                "os_name": "Linux",
                "kernel_version": "unknown",
                "uptime_seconds": 0.0,
                "boot_time": 0.0,
                "load_avg": [0.0, 0.0, 0.0],
                "process_count": 0,
                "error": str(e),
            }

    @classmethod
    def collect_full_metrics(cls) -> Dict[str, Any]:
        cpu = cls.get_cpu_info()
        mem = cls.get_memory_info()
        disk = cls.get_disk_info()
        net = cls.get_network_info()
        sys_info = cls.get_system_summary()

        health = "healthy"
        if cpu.get("cpu_percent", 0) > 90 or mem.get("ram_percent", 0) > 92 or disk.get("disk_percent", 0) > 95:
            health = "critical"
        elif cpu.get("cpu_percent", 0) > 75 or mem.get("ram_percent", 0) > 80 or disk.get("disk_percent", 0) > 85:
            health = "warning"

        return {
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            **cpu,
            **mem,
            **disk,
            **net,
            **sys_info,
            "status": health,
        }
