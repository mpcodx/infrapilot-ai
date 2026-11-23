from fastapi import APIRouter, Query, HTTPException
from backend.app.monitoring.linux_collector import LinuxCollector
from backend.app.monitoring.discovery import DiscoveryService
from backend.app.diagnostics.capacity import CapacityEngine

router = APIRouter()


@router.get("/performance/report")
def get_performance_report():
    metrics = LinuxCollector.collect_full_metrics()
    processes = DiscoveryService.get_processes(limit=10)
    containers = DiscoveryService.get_containers()
    return CapacityEngine.analyze(metrics=metrics, processes=processes, containers=containers)


@router.post("/diagnostics/run")
def run_diagnostics():
    metrics = LinuxCollector.collect_full_metrics()
    processes = DiscoveryService.get_processes(limit=15)
    containers = DiscoveryService.get_containers()
    analysis = CapacityEngine.analyze(metrics=metrics, processes=processes, containers=containers)

    return {
        "status": "success",
        "system_status": metrics.get("status", "healthy"),
        "analysis": analysis,
        "top_processes": processes[:5],
    }


@router.post("/performance/benchmark")
def run_performance_benchmark(duration: int = Query(3, ge=1, le=5)):
    return CapacityEngine.run_bounded_benchmark(duration_seconds=duration)
