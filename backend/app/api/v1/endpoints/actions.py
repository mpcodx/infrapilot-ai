from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from backend.app.schemas.schemas import ActionPreviewRequest, ActionPreviewResponse, ActionApproveRequest
from backend.app.services.action_engine import SafeActionEngine
from backend.app.core.database import get_db
from backend.app.models.models import AuditLog, ApprovedAction
import datetime

router = APIRouter()


@router.post("/actions/preview", response_model=ActionPreviewResponse)
def preview_action(req: ActionPreviewRequest, db: Session = Depends(get_db)):
    try:
        preview = SafeActionEngine.create_preview(action_type=req.action_type, target=req.target)
        now_utc = datetime.datetime.now(datetime.timezone.utc)
        expires_utc = datetime.datetime.fromisoformat(preview["expires_at"])
        
        # Store in DB as well
        app_action = ApprovedAction(
            action_id=preview["action_id"],
            action_type=preview["action_type"],
            target=preview["target"],
            command_preview=preview["command_preview"],
            requested_at=now_utc,
            expires_at=expires_utc,
            status="pending",
        )
        db.add(app_action)
        db.commit()
        return preview
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/actions/approve")
def approve_action(req: ActionApproveRequest, db: Session = Depends(get_db)):
    if not req.confirmed:
        raise HTTPException(status_code=400, detail="Action approval was not confirmed.")

    try:
        res = SafeActionEngine.execute_approved_action(action_id=req.action_id)
        now_utc = datetime.datetime.now(datetime.timezone.utc)
        
        # Log to audit log
        audit = AuditLog(
            actor="operator",
            action_type=res.get("status", "unknown"),
            target=req.action_id,
            status=res.get("status", "unknown"),
            output=res.get("output", "") or res.get("error", ""),
            approved_by="operator",
            approved_at=now_utc,
        )
        db.add(audit)

        # Update action
        act = db.query(ApprovedAction).filter(ApprovedAction.action_id == req.action_id).first()
        if act:
            act.status = res.get("status")
            act.approved_at = now_utc
            act.executed_at = now_utc
            act.result_output = res.get("output")
            act.error_message = res.get("error")

        db.commit()
        return res
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
