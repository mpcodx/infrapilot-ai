import asyncio
import logging
import datetime
from sqlalchemy.orm import Session
from backend.app.core.database import SessionLocal
from backend.app.models.models import (
    ManagedServer,
    SystemSnapshot,
    SecurityFinding,
    utc_now,
)
from backend.app.services.ssh_service import SSHService

logger = logging.getLogger("infrapilot-remote-monitor")
_semaphore = asyncio.Semaphore(5)


async def poll_single_server(server_id: str):
    """Poll a single server for discovery and metrics within bounded concurrency."""
    async with _semaphore:
        db: Session = SessionLocal()
        try:
            server = db.query(ManagedServer).filter(ManagedServer.server_id == server_id).first()
            if not server or not server.is_host_key_trusted:
                return

            # Check if interval has elapsed
            now = utc_now()
            if server.last_connected_at:
                elapsed = (now - server.last_connected_at).total_seconds()
                if elapsed < server.polling_interval:
                    return

            try:
                data = await SSHService.discover_server(server)

                # Update server state
                server.status = "online"
                server.last_connected_at = now
                server.last_error = None
                server.system_info = {
                    "hostname": data.get("hostname"),
                    "os_name": data.get("os_name"),
                    "os_version": data.get("os_version"),
                    "kernel_version": data.get("kernel_version"),
                    "architecture": data.get("architecture"),
                    "cpu_model": data.get("cpu_model"),
                    "cpu_count": data.get("cpu_count"),
                }

                # Save snapshot
                snapshot = SystemSnapshot(
                    server_id=server.server_id,
                    timestamp=now,
                    cpu_percent=data.get("cpu_percent", 0.0),
                    cpu_count=data.get("cpu_count", 1),
                    ram_total=data.get("ram_total", 0),
                    ram_used=data.get("ram_used", 0),
                    ram_available=data.get("ram_available", 0),
                    ram_percent=data.get("ram_percent", 0.0),
                    swap_total=data.get("swap_total", 0),
                    swap_used=data.get("swap_used", 0),
                    swap_percent=data.get("swap_percent", 0.0),
                    disk_total=data.get("disk_total", 0),
                    disk_used=data.get("disk_used", 0),
                    disk_free=data.get("disk_free", 0),
                    disk_percent=data.get("disk_percent", 0.0),
                    hostname=data.get("hostname"),
                    os_name=data.get("os_name"),
                    kernel_version=data.get("kernel_version"),
                    uptime_seconds=data.get("uptime_seconds", 0.0),
                    load_avg=data.get("load_avg"),
                    net_bytes_sent=data.get("net_bytes_sent", 0),
                    net_bytes_recv=data.get("net_bytes_recv", 0),
                    status="healthy" if data.get("cpu_percent", 0) < 90 else "warning",
                )
                db.add(snapshot)

                # Upsert security findings
                for f in data.get("security_findings", []):
                    existing = db.query(SecurityFinding).filter(
                        SecurityFinding.finding_id == f["finding_id"]
                    ).first()
                    if not existing:
                        db.add(SecurityFinding(
                            server_id=server.server_id,
                            finding_id=f["finding_id"],
                            severity=f["severity"],
                            category=f["category"],
                            title=f["title"],
                            description=f["description"],
                            affected_component=f["affected_component"],
                            evidence=f.get("evidence"),
                            recommended_fix=f.get("recommended_fix"),
                            timestamp=now,
                            status="open",
                        ))

                db.commit()
                logger.info(f"Successfully polled remote server {server.name} ({server.hostname})")

            except Exception as e:
                db.rollback()
                server.status = "offline"
                server.last_error = str(e)
                db.commit()
                logger.warning(f"Failed to poll remote server {server.name}: {e}")

        finally:
            db.close()


async def remote_monitoring_loop():
    """Continuous polling loop for registered remote servers."""
    while True:
        try:
            db: Session = SessionLocal()
            try:
                servers = db.query(ManagedServer).filter(
                    ManagedServer.status != "disabled",
                    ManagedServer.is_host_key_trusted == True,
                ).all()
                server_ids = [s.server_id for s in servers]
            finally:
                db.close()

            if server_ids:
                tasks = [poll_single_server(sid) for sid in server_ids]
                await asyncio.gather(*tasks, return_exceptions=True)

        except Exception as e:
            logger.error(f"Error in remote monitoring cycle: {e}")

        await asyncio.sleep(5)
