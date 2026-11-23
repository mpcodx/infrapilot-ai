import time
import datetime
import math
from typing import Dict, Any, List


class CapacityEngine:
    @staticmethod
    def analyze(metrics: Dict[str, Any], processes: List[Dict[str, Any]], containers: List[Dict[str, Any]]) -> Dict[str, Any]:
        cpu_pct = metrics.get("cpu_percent", 0.0)
        ram_pct = metrics.get("ram_percent", 0.0)
        ram_avail = metrics.get("ram_available", 0)
        ram_total = metrics.get("ram_total", 1)
        disk_pct = metrics.get("disk_percent", 0.0)
        disk_free = metrics.get("disk_free", 0)
        disk_total = metrics.get("disk_total", 1)

        cpu_headroom = max(0.0, 100.0 - cpu_pct)
        ram_headroom_pct = max(0.0, 100.0 - ram_pct)
        disk_headroom_pct = max(0.0, 100.0 - disk_pct)

        bottlenecks = []
        recommendations = []

        if cpu_pct > 80:
            bottlenecks.append(f"High CPU utilization ({cpu_pct:.1f}%)")
            recommendations.append("Investigate high CPU consumer processes or scale CPU cores.")
        elif cpu_pct > 60:
            recommendations.append("CPU usage is elevated; monitor for sustained load peaks.")

        if ram_pct > 85:
            bottlenecks.append(f"Memory saturation risk (RAM usage {ram_pct:.1f}%)")
            recommendations.append("Free memory or tune resident process memory footprints to prevent OOM killer activation.")
        elif ram_pct > 75:
            recommendations.append("RAM consumption exceeds 75%; plan capacity headroom.")

        if disk_pct > 90:
            bottlenecks.append(f"Critical disk storage utilization ({disk_pct:.1f}%)")
            recommendations.append("Purge old logs, unused Docker images/volumes, and expand disk volume.")
        elif disk_pct > 80:
            recommendations.append("Disk space is below 20% available; perform routine maintenance.")

        # Analyze top process
        if processes:
            top_proc = processes[0]
            if top_proc.get("cpu_percent", 0) > 40:
                bottlenecks.append(f"Process '{top_proc.get('name')}' (PID {top_proc.get('pid')}) is consuming {top_proc.get('cpu_percent')}% CPU.")
                recommendations.append(f"Inspect runtime profile of '{top_proc.get('name')}'.")

        # Analyze container health & restarts
        for c in containers:
            if c.get("restart_count", 0) > 3:
                bottlenecks.append(f"Container '{c.get('name')}' has restarted {c.get('restart_count')} times.")
                recommendations.append(f"Inspect container logs for crashes: docker logs {c.get('name')}")

        if not bottlenecks:
            bottlenecks.append("No active hardware or resource bottlenecks detected.")
            recommendations.append("System is operating within healthy performance thresholds.")

        assumptions = (
            "Headroom estimations assume current workload baseline behavior without sudden "
            "traffic spikes or unconstrained batch processing jobs."
        )

        return {
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "cpu_headroom_percent": round(cpu_headroom, 1),
            "ram_headroom_bytes": ram_avail,
            "ram_headroom_percent": round(ram_headroom_pct, 1),
            "disk_headroom_bytes": disk_free,
            "disk_headroom_percent": round(disk_headroom_pct, 1),
            "bottlenecks": bottlenecks,
            "recommendations": recommendations,
            "assumptions": assumptions,
        }

    @staticmethod
    def run_bounded_benchmark(duration_seconds: int = 3) -> Dict[str, Any]:
        """A safe, strictly bounded computational test (capped at max 5s) to assess single-core speed."""
        duration = min(max(duration_seconds, 1), 5)
        start = time.perf_counter()
        ops = 0
        end_time = start + duration

        while time.perf_counter() < end_time:
            # Safe math benchmark without memory allocation
            _ = math.sqrt(ops + 1.234)
            ops += 1

        elapsed = time.perf_counter() - start
        ops_per_sec = ops / elapsed if elapsed > 0 else 0

        return {
            "duration_requested": duration,
            "duration_actual": round(elapsed, 3),
            "total_operations": ops,
            "operations_per_second": round(ops_per_sec, 2),
            "warning": "Bounded non-destructive benchmark. Run only during operator evaluation.",
            "completed_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }
