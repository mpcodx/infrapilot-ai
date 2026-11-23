from fastapi import APIRouter, Query
from typing import Optional
from backend.app.monitoring.discovery import DiscoveryService

router = APIRouter()


@router.get("/processes")
def list_processes(
    limit: int = Query(50, ge=1, le=200),
    search: Optional[str] = Query(None, max_length=50)
):
    procs = DiscoveryService.get_processes(limit=limit)
    if search:
        search_lower = search.lower()
        procs = [
            p for p in procs
            if search_lower in p.get("name", "").lower()
            or search_lower in str(p.get("pid", ""))
            or search_lower in p.get("username", "").lower()
        ]
    return procs


@router.get("/services")
def list_services(
    active_only: bool = Query(False),
    search: Optional[str] = Query(None, max_length=50)
):
    services = DiscoveryService.get_services()
    if active_only:
        services = [s for s in services if s.get("is_active")]
    if search:
        search_lower = search.lower()
        services = [s for s in services if search_lower in s.get("name", "").lower()]
    return services


@router.get("/ports")
def list_ports(
    protocol: Optional[str] = Query(None, pattern="^(tcp|udp)$"),
    search: Optional[str] = Query(None, max_length=50)
):
    ports = DiscoveryService.get_ports()
    if protocol:
        ports = [p for p in ports if p.get("protocol") == protocol.lower()]
    if search:
        search_lower = search.lower()
        ports = [
            p for p in ports
            if search_lower in str(p.get("local_port", ""))
            or (p.get("process_name") and search_lower in p.get("process_name", "").lower())
        ]
    return ports


@router.get("/containers")
def list_containers(
    status: Optional[str] = Query(None, max_length=20)
):
    containers = DiscoveryService.get_containers()
    if status:
        containers = [c for c in containers if c.get("status", "").lower() == status.lower()]
    return containers
