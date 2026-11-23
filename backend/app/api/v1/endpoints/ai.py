from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Dict, Any, List

from backend.app.core.database import get_db
from backend.app.schemas.schemas import AIChatRequest, AIChatResponse
from backend.app.ai.ollama_service import ollama_service
from backend.app.monitoring.linux_collector import LinuxCollector
from backend.app.security.auditor import SecurityAuditor
from backend.app.monitoring.discovery import DiscoveryService
from backend.app.models.models import ManagedServer, SystemSnapshot, SecurityFinding

router = APIRouter()


@router.post("/ai/chat", response_model=AIChatResponse)
async def ai_chat(req: AIChatRequest, db: Session = Depends(get_db)):
    context = req.context or {}

    # Multi-server context inclusion
    if req.all_servers or req.server_ids or "server" in req.message.lower():
        query = db.query(ManagedServer)
        if req.server_ids:
            query = query.filter(ManagedServer.server_id.in_(req.server_ids))
        servers = query.all()

        server_summaries: List[Dict[str, Any]] = []
        for s in servers:
            latest_snap = db.query(SystemSnapshot).filter(
                SystemSnapshot.server_id == s.server_id
            ).order_by(SystemSnapshot.timestamp.desc()).first()

            findings_count = db.query(SecurityFinding).filter(
                SecurityFinding.server_id == s.server_id,
                SecurityFinding.status == "open",
            ).count()

            server_summaries.append({
                "server_id": s.server_id,
                "name": s.name,
                "hostname": s.hostname,
                "environment": s.environment,
                "status": s.status,
                "cpu_percent": latest_snap.cpu_percent if latest_snap else None,
                "ram_percent": latest_snap.ram_percent if latest_snap else None,
                "disk_percent": latest_snap.disk_percent if latest_snap else None,
                "open_security_findings": findings_count,
                "last_connected": s.last_connected_at.isoformat() if s.last_connected_at else None,
            })
        context["servers_inventory"] = server_summaries

    # Single server context inclusion
    elif req.server_id:
        server = db.query(ManagedServer).filter(ManagedServer.server_id == req.server_id).first()
        if server:
            latest_snap = db.query(SystemSnapshot).filter(
                SystemSnapshot.server_id == server.server_id
            ).order_by(SystemSnapshot.timestamp.desc()).first()

            findings = db.query(SecurityFinding).filter(
                SecurityFinding.server_id == server.server_id,
                SecurityFinding.status == "open",
            ).limit(5).all()

            context["selected_server"] = {
                "server_id": server.server_id,
                "name": server.name,
                "hostname": server.hostname,
                "environment": server.environment,
                "status": server.status,
                "system_info": server.system_info,
                "metrics": {
                    "cpu_percent": latest_snap.cpu_percent if latest_snap else None,
                    "ram_percent": latest_snap.ram_percent if latest_snap else None,
                    "disk_percent": latest_snap.disk_percent if latest_snap else None,
                } if latest_snap else None,
                "findings": [f.title for f in findings],
            }

    # Default: include local host context
    elif req.include_system_context:
        metrics = LinuxCollector.collect_full_metrics()
        ports = DiscoveryService.get_ports()
        findings = SecurityAuditor.run_full_audit(ports=ports)
        context["metrics"] = metrics
        context["findings"] = findings[:3]

    result = await ollama_service.generate_response(query=req.message, context=context)
    return AIChatResponse(
        response=result["response"],
        model=result["model"],
        evidence=result.get("evidence", []),
        suggested_commands=result.get("suggested_commands", []),
        warnings=result.get("warnings", []),
        is_fallback=result.get("is_fallback", False),
    )
