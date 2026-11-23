import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.models.models import SystemSnapshot
from backend.app.monitoring.linux_collector import LinuxCollector

router = APIRouter()


@router.get("/health")
def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "service": "InfraPilot AI Backend",
    }


@router.get("/system/metrics")
def get_current_metrics(db: Session = Depends(get_db)):
    metrics = LinuxCollector.collect_full_metrics()
    
    # Save snapshot to database
    try:
        snap = SystemSnapshot(
            cpu_percent=metrics["cpu_percent"],
            cpu_count=metrics["cpu_count"],
            cpu_freq_current=metrics.get("cpu_freq_current"),
            per_cpu_percent=metrics.get("per_cpu_percent"),
            ram_total=metrics["ram_total"],
            ram_used=metrics["ram_used"],
            ram_available=metrics["ram_available"],
            ram_percent=metrics["ram_percent"],
            swap_total=metrics.get("swap_total"),
            swap_used=metrics.get("swap_used"),
            swap_percent=metrics.get("swap_percent"),
            disk_total=metrics["disk_total"],
            disk_used=metrics["disk_used"],
            disk_free=metrics["disk_free"],
            disk_percent=metrics["disk_percent"],
            disk_io={"read_bytes_sec": metrics.get("read_bytes_sec", 0), "write_bytes_sec": metrics.get("write_bytes_sec", 0)},
            net_bytes_sent=metrics.get("net_bytes_sent"),
            net_bytes_recv=metrics.get("net_bytes_recv"),
            net_io={"upload_rate": metrics.get("upload_rate_bps", 0), "download_rate": metrics.get("download_rate_bps", 0)},
            hostname=metrics.get("hostname"),
            os_name=metrics.get("os_name"),
            kernel_version=metrics.get("kernel_version"),
            uptime_seconds=metrics.get("uptime_seconds"),
            load_avg=metrics.get("load_avg"),
            status=metrics.get("status", "healthy"),
        )
        db.add(snap)
        db.commit()
    except Exception:
        db.rollback()

    return metrics


@router.get("/system/overview")
def get_system_overview(db: Session = Depends(get_db)):
    metrics = LinuxCollector.collect_full_metrics()
    return {
        "metrics": metrics,
        "mode": "standalone_host",
        "engine": "psutil_v7",
    }


@router.get("/system/metrics/history")
def get_metrics_history(
    limit: int = Query(60, ge=5, le=1000),
    db: Session = Depends(get_db)
):
    snapshots = (
        db.query(SystemSnapshot)
        .order_by(SystemSnapshot.timestamp.desc())
        .limit(limit)
        .all()
    )
    # Reverse to chronological order
    snapshots.reverse()
    return [
        {
            "timestamp": s.timestamp.isoformat() if s.timestamp else datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "cpu_percent": s.cpu_percent,
            "ram_percent": s.ram_percent,
            "disk_percent": s.disk_percent,
            "uptime_seconds": s.uptime_seconds,
        }
        for s in snapshots
    ]
