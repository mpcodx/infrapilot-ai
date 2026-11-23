import hashlib
import uuid
import datetime
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.core.config import settings
from backend.app.models.models import RegisteredAgent
from backend.app.schemas.schemas import AgentRegisterRequest, AgentRegisterResponse, AgentHeartbeatRequest

router = APIRouter()


@router.post("/agents/register", response_model=AgentRegisterResponse)
def register_agent(req: AgentRegisterRequest, db: Session = Depends(get_db)):
    if req.shared_secret != settings.AGENT_SHARED_SECRET:
        raise HTTPException(status_code=403, detail="Invalid agent registration secret.")

    agent_id = f"AGENT-{uuid.uuid4().hex[:8]}"
    raw_token = uuid.uuid4().hex
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    now_utc = datetime.datetime.now(datetime.timezone.utc)

    agent = RegisteredAgent(
        agent_id=agent_id,
        hostname=req.hostname,
        os_info=req.os_info,
        ip_address=req.ip_address,
        capabilities=req.capabilities,
        auth_token_hash=token_hash,
        registered_at=now_utc,
        last_heartbeat=now_utc,
        status="online",
    )
    db.add(agent)
    db.commit()

    return AgentRegisterResponse(agent_id=agent_id, token=raw_token, status="registered")


@router.get("/agents")
def list_agents(db: Session = Depends(get_db)):
    agents = db.query(RegisteredAgent).all()
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    
    # Check for disconnect / offline status (60s threshold)
    updated = False
    for a in agents:
        if a.last_heartbeat:
            # Normalize naive / aware
            hb = a.last_heartbeat
            if hb.tzinfo is None:
                hb = hb.replace(tzinfo=datetime.timezone.utc)
            if (now_utc - hb).total_seconds() > 60:
                if a.status != "offline":
                    a.status = "offline"
                    updated = True

    if updated:
        db.commit()

    return [
        {
            "agent_id": a.agent_id,
            "hostname": a.hostname,
            "os_info": a.os_info,
            "ip_address": a.ip_address,
            "registered_at": a.registered_at.isoformat() if a.registered_at else None,
            "last_heartbeat": a.last_heartbeat.isoformat() if a.last_heartbeat else None,
            "status": a.status,
            "capabilities": a.capabilities or [],
        }
        for a in agents
    ]


@router.post("/agents/heartbeat")
def agent_heartbeat(req: AgentHeartbeatRequest, db: Session = Depends(get_db)):
    token_hash = hashlib.sha256(req.token.encode("utf-8")).hexdigest()
    agent = db.query(RegisteredAgent).filter(
        RegisteredAgent.agent_id == req.agent_id,
        RegisteredAgent.auth_token_hash == token_hash
    ).first()

    if not agent:
        raise HTTPException(status_code=401, detail="Unauthorized agent token or ID.")

    now_utc = datetime.datetime.now(datetime.timezone.utc)
    agent.last_heartbeat = now_utc
    agent.status = "online"
    db.commit()

    return {"status": "acknowledged", "timestamp": now_utc.isoformat()}
