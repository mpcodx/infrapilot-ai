import uuid
import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.encryption import encrypt_secret, mask_credential
from backend.app.models.models import (
    ManagedServer,
    SystemSnapshot,
    ApprovedAction,
    AuditLog,
    utc_now,
)
from backend.app.schemas.schemas import (
    ServerCreate,
    ServerUpdate,
    ServerResponse,
    ServerTestRequest,
    ServerTestResponse,
    ServerTrustHostKeyRequest,
    ActionPreviewRequest,
    ActionPreviewResponse,
    ActionApproveRequest,
    ActionApproveResponse,
)
from backend.app.services.ssh_service import SSHService

router = APIRouter()


def _format_server_response(server: ManagedServer) -> ServerResponse:
    return ServerResponse(
        server_id=server.server_id,
        name=server.name,
        connection_type=server.connection_type,
        hostname=server.hostname,
        ssh_port=server.ssh_port,
        username=server.username,
        auth_method=server.auth_method,
        has_credential=bool(server.encrypted_credential),
        has_passphrase=bool(server.encrypted_passphrase),
        timeout_seconds=server.timeout_seconds,
        environment=server.environment,
        organization=server.organization,
        tags=server.tags or [],
        host_key_fingerprint=server.host_key_fingerprint,
        host_key_type=server.host_key_type,
        is_host_key_trusted=server.is_host_key_trusted,
        status=server.status,
        last_connected_at=server.last_connected_at,
        last_error=server.last_error,
        polling_interval=server.polling_interval,
        system_info=server.system_info,
        created_at=server.created_at,
        updated_at=server.updated_at,
    )


@router.get("", response_model=List[ServerResponse])
def list_servers(
    environment: Optional[str] = None,
    organization: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """List all registered servers with connection health and metadata."""
    query = db.query(ManagedServer)
    if environment:
        query = query.filter(ManagedServer.environment == environment)
    if organization:
        query = query.filter(ManagedServer.organization == organization)
    servers = query.order_by(ManagedServer.created_at.desc()).all()
    return [_format_server_response(s) for s in servers]


@router.post("", response_model=ServerResponse, status_code=201)
async def create_server(req: ServerCreate, db: Session = Depends(get_db)):
    """Register a new remote server via SSH Direct or Agent."""
    server_id = f"srv-{uuid.uuid4().hex[:12]}"

    encrypted_cred = encrypt_secret(req.credential) if req.credential else None
    encrypted_pass = encrypt_secret(req.passphrase) if req.passphrase else None

    # Probe host key and test connection if SSH
    host_key_fp = None
    host_key_type = None
    is_trusted = req.auto_trust_host_key
    initial_status = "disconnected"

    if req.connection_type == "ssh":
        test_res = await SSHService.test_connection(
            hostname=req.hostname,
            port=req.ssh_port,
            username=req.username,
            auth_method=req.auth_method,
            credential=req.credential,
            passphrase=req.passphrase,
            timeout=req.timeout_seconds,
            allow_first_trust=req.auto_trust_host_key,
        )
        host_key_fp = test_res.get("host_key_fingerprint")
        host_key_type = test_res.get("host_key_type")
        if test_res.get("success"):
            initial_status = "online"
            is_trusted = True
        elif host_key_fp and not req.auto_trust_host_key:
            initial_status = "untrusted_host_key"

    server = ManagedServer(
        server_id=server_id,
        name=req.name,
        connection_type=req.connection_type,
        hostname=req.hostname,
        ssh_port=req.ssh_port,
        username=req.username,
        auth_method=req.auth_method,
        encrypted_credential=encrypted_cred,
        encrypted_passphrase=encrypted_pass,
        timeout_seconds=req.timeout_seconds,
        environment=req.environment,
        organization=req.organization,
        tags=req.tags,
        host_key_fingerprint=host_key_fp,
        host_key_type=host_key_type,
        is_host_key_trusted=is_trusted,
        status=initial_status,
        last_connected_at=utc_now() if initial_status == "online" else None,
    )
    db.add(server)
    db.commit()
    db.refresh(server)
    return _format_server_response(server)


@router.get("/{server_id}", response_model=ServerResponse)
def get_server(server_id: str, db: Session = Depends(get_db)):
    """Retrieve details for a specific registered server."""
    server = db.query(ManagedServer).filter(ManagedServer.server_id == server_id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    return _format_server_response(server)


@router.put("/{server_id}", response_model=ServerResponse)
def update_server(server_id: str, req: ServerUpdate, db: Session = Depends(get_db)):
    """Update server configuration and rotate credentials securely."""
    server = db.query(ManagedServer).filter(ManagedServer.server_id == server_id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    if req.name is not None:
        server.name = req.name
    if req.hostname is not None:
        server.hostname = req.hostname
    if req.ssh_port is not None:
        server.ssh_port = req.ssh_port
    if req.username is not None:
        server.username = req.username
    if req.auth_method is not None:
        server.auth_method = req.auth_method
    if req.timeout_seconds is not None:
        server.timeout_seconds = req.timeout_seconds
    if req.environment is not None:
        server.environment = req.environment
    if req.organization is not None:
        server.organization = req.organization
    if req.tags is not None:
        server.tags = req.tags
    if req.polling_interval is not None:
        server.polling_interval = req.polling_interval

    # Rotate credentials if provided
    if req.credential is not None:
        server.encrypted_credential = encrypt_secret(req.credential)
    if req.passphrase is not None:
        server.encrypted_passphrase = encrypt_secret(req.passphrase)

    server.updated_at = utc_now()
    db.commit()
    db.refresh(server)
    return _format_server_response(server)


@router.delete("/{server_id}")
def delete_server(server_id: str, db: Session = Depends(get_db)):
    """Remove server registration and permanently revoke stored credentials."""
    server = db.query(ManagedServer).filter(ManagedServer.server_id == server_id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    db.delete(server)
    db.commit()
    return {"message": f"Server {server_id} removed and credentials revoked."}


@router.post("/test", response_model=ServerTestResponse)
async def test_adhoc_connection(req: ServerTestRequest):
    """Test SSH connectivity ad-hoc before saving credentials."""
    res = await SSHService.test_connection(
        hostname=req.hostname,
        port=req.ssh_port,
        username=req.username,
        auth_method=req.auth_method,
        credential=req.credential,
        passphrase=req.passphrase,
        timeout=req.timeout_seconds,
        allow_first_trust=True,
    )
    return ServerTestResponse(
        success=res["success"],
        message=res["message"],
        host_key_fingerprint=res.get("host_key_fingerprint"),
        host_key_type=res.get("host_key_type"),
        is_host_key_trusted=res.get("is_host_key_trusted", False),
        latency_ms=res.get("latency_ms"),
        details=res.get("details"),
    )


@router.post("/{server_id}/test", response_model=ServerTestResponse)
async def test_saved_server(server_id: str, db: Session = Depends(get_db)):
    """Test connection using stored, encrypted credentials for an existing server."""
    server = db.query(ManagedServer).filter(ManagedServer.server_id == server_id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    from backend.app.core.encryption import decrypt_secret
    raw_cred = decrypt_secret(server.encrypted_credential) if server.encrypted_credential else None
    raw_pass = decrypt_secret(server.encrypted_passphrase) if server.encrypted_passphrase else None

    res = await SSHService.test_connection(
        hostname=server.hostname,
        port=server.ssh_port,
        username=server.username,
        auth_method=server.auth_method,
        credential=raw_cred,
        passphrase=raw_pass,
        timeout=server.timeout_seconds,
        expected_fingerprint=server.host_key_fingerprint if server.is_host_key_trusted else None,
        allow_first_trust=server.is_host_key_trusted,
    )

    if res["success"]:
        server.status = "online"
        server.last_connected_at = utc_now()
        server.last_error = None
    else:
        server.status = "offline"
        server.last_error = res["message"]
    db.commit()

    return ServerTestResponse(
        success=res["success"],
        message=res["message"],
        host_key_fingerprint=res.get("host_key_fingerprint"),
        host_key_type=res.get("host_key_type"),
        is_host_key_trusted=res.get("is_host_key_trusted", False),
        latency_ms=res.get("latency_ms"),
        details=res.get("details"),
    )


@router.post("/{server_id}/trust-host-key")
def trust_host_key(server_id: str, req: ServerTrustHostKeyRequest, db: Session = Depends(get_db)):
    """Explicitly trust the remote server's SSH host key fingerprint."""
    server = db.query(ManagedServer).filter(ManagedServer.server_id == server_id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    if req.fingerprint:
        server.host_key_fingerprint = req.fingerprint
    server.is_host_key_trusted = True
    server.status = "disconnected"
    db.commit()
    return {"message": "Host key explicitly trusted by operator", "fingerprint": server.host_key_fingerprint}


@router.post("/{server_id}/discover")
async def trigger_discovery(server_id: str, db: Session = Depends(get_db)):
    """Trigger immediate, on-demand full discovery and telemetry refresh via SSH."""
    server = db.query(ManagedServer).filter(ManagedServer.server_id == server_id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    if not server.is_host_key_trusted:
        raise HTTPException(status_code=400, detail="Host key must be verified and trusted before running discovery.")

    try:
        data = await SSHService.discover_server(server)
        server.status = "online"
        server.last_connected_at = utc_now()
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
        db.commit()
        return {"success": True, "data": data}
    except Exception as e:
        server.status = "offline"
        server.last_error = str(e)
        db.commit()
        raise HTTPException(status_code=500, detail=f"Discovery failed: {str(e)}")


@router.get("/{server_id}/metrics")
def get_server_metrics(server_id: str, limit: int = Query(50, ge=1, le=500), db: Session = Depends(get_db)):
    """Retrieve historical telemetry snapshots for this server."""
    snapshots = db.query(SystemSnapshot).filter(
        SystemSnapshot.server_id == server_id
    ).order_by(SystemSnapshot.timestamp.desc()).limit(limit).all()
    return snapshots


@router.post("/{server_id}/action/preview", response_model=ActionPreviewResponse)
def preview_remote_action(server_id: str, req: ActionPreviewRequest, db: Session = Depends(get_db)):
    """Preview a safe remediation action for a remote server and generate an approval token."""
    server = db.query(ManagedServer).filter(ManagedServer.server_id == server_id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    # Target regex validation
    import re
    if not re.match(r"^[a-zA-Z0-9_\-\.@]{1,64}$", req.target):
        raise HTTPException(status_code=400, detail="Target format rejected by whitelist validation regex.")

    templates = {
        "restart_service": f"ssh {server.username}@{server.hostname} systemctl restart {req.target}",
        "stop_service": f"ssh {server.username}@{server.hostname} systemctl stop {req.target}",
        "start_service": f"ssh {server.username}@{server.hostname} systemctl start {req.target}",
        "restart_container": f"ssh {server.username}@{server.hostname} docker restart {req.target}",
        "stop_container": f"ssh {server.username}@{server.hostname} docker stop {req.target}",
        "container_logs": f"ssh {server.username}@{server.hostname} docker logs --tail 100 {req.target}",
        "clean_docker_images": f"ssh {server.username}@{server.hostname} docker image prune -f",
    }
    if req.action_type not in templates:
        raise HTTPException(status_code=400, detail="Unknown or unauthorized action type.")

    action_id = f"act-{uuid.uuid4().hex[:12]}"
    preview = templates[req.action_type]
    now = utc_now()
    expires = now + datetime.timedelta(minutes=5)

    approved_action = ApprovedAction(
        server_id=server.server_id,
        action_id=action_id,
        action_type=req.action_type,
        target=req.target,
        command_preview=preview,
        requested_at=now,
        expires_at=expires,
        status="pending",
    )
    db.add(approved_action)
    db.commit()

    return ActionPreviewResponse(
        action_id=action_id,
        action_type=req.action_type,
        target=req.target,
        command_preview=preview,
        risk_level="medium" if "stop" in req.action_type else "low",
        description=f"Remote operation '{req.action_type}' targeting {req.target} on {server.name}",
        expires_at=expires.isoformat(),
        requires_approval=True,
    )


@router.post("/{server_id}/action/approve", response_model=ActionApproveResponse)
async def approve_remote_action(server_id: str, req: ActionApproveRequest, db: Session = Depends(get_db)):
    """Operator approval and remote execution of a previewed action over SSH."""
    server = db.query(ManagedServer).filter(ManagedServer.server_id == server_id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    action = db.query(ApprovedAction).filter(
        ApprovedAction.action_id == req.action_id,
        ApprovedAction.server_id == server.server_id,
    ).first()
    if not action:
        raise HTTPException(status_code=404, detail="Approval token not found")

    if action.status != "pending":
        raise HTTPException(status_code=400, detail=f"Action is already '{action.status}'. Replay rejected.")

    now = utc_now()
    if action.expires_at and action.expires_at.replace(tzinfo=datetime.timezone.utc) < now:
        action.status = "expired"
        db.commit()
        raise HTTPException(status_code=400, detail="Action token has expired. Please re-preview.")

    action.status = "executing"
    action.approved_at = now
    db.commit()

    try:
        res = await SSHService.execute_approved_remote_action(
            server=server, action_type=action.action_type, target=action.target
        )
        action.status = "completed" if res["success"] else "failed"
        action.executed_at = utc_now()
        action.result_output = res["stdout"] or res["stderr"]

        # Audit log
        db.add(AuditLog(
            actor="operator",
            action_type=action.action_type,
            target=f"{server.name}:{action.target}",
            parameters={"server_id": server.server_id, "action_id": action.action_id},
            status=action.status,
            output=action.result_output[:1000],
            approved_by="operator",
            approved_at=now,
        ))
        db.commit()

        return ActionApproveResponse(
            action_id=action.action_id,
            status=action.status,
            output=res["stdout"],
            error=res["stderr"] if not res["success"] else None,
            executed_at=action.executed_at,
        )
    except Exception as e:
        action.status = "failed"
        action.error_message = str(e)
        db.commit()
        raise HTTPException(status_code=500, detail=f"Remote execution failed: {str(e)}")
