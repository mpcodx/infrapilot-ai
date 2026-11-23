from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.models.models import SecurityFinding
from backend.app.security.auditor import SecurityAuditor
from backend.app.monitoring.discovery import DiscoveryService
import datetime

router = APIRouter()


@router.get("/security/findings")
def get_security_findings(db: Session = Depends(get_db)):
    db_findings = db.query(SecurityFinding).order_by(SecurityFinding.timestamp.desc()).all()
    if not db_findings:
        # Run baseline scan if no findings saved yet
        ports = DiscoveryService.get_ports()
        scanned = SecurityAuditor.run_full_audit(ports=ports)
        for s in scanned:
            sf = SecurityFinding(
                finding_id=s["finding_id"],
                severity=s["severity"],
                category=s["category"],
                title=s["title"],
                description=s["description"],
                affected_component=s["affected_component"],
                evidence=s.get("evidence"),
                explanation=s.get("explanation"),
                recommended_fix=s.get("recommended_fix"),
                confidence=s.get("confidence", 1.0),
                status=s.get("status", "open"),
            )
            db.add(sf)
        db.commit()
        db_findings = db.query(SecurityFinding).order_by(SecurityFinding.timestamp.desc()).all()

    return [
        {
            "finding_id": f.finding_id,
            "severity": f.severity,
            "category": f.category,
            "title": f.title,
            "description": f.description,
            "affected_component": f.affected_component,
            "evidence": f.evidence,
            "explanation": f.explanation,
            "recommended_fix": f.recommended_fix,
            "confidence": f.confidence,
            "timestamp": f.timestamp.isoformat(),
            "status": f.status,
        }
        for f in db_findings
    ]


@router.post("/security/scan")
def trigger_security_scan(db: Session = Depends(get_db)):
    ports = DiscoveryService.get_ports()
    fresh_findings = SecurityAuditor.run_full_audit(ports=ports)
    
    # Clean previous findings or update
    db.query(SecurityFinding).delete()
    for s in fresh_findings:
        sf = SecurityFinding(
            finding_id=s["finding_id"],
            severity=s["severity"],
            category=s["category"],
            title=s["title"],
            description=s["description"],
            affected_component=s["affected_component"],
            evidence=s.get("evidence"),
            explanation=s.get("explanation"),
            recommended_fix=s.get("recommended_fix"),
            confidence=s.get("confidence", 1.0),
            status=s.get("status", "open"),
        )
        db.add(sf)
    db.commit()

    return {
        "status": "success",
        "scanned_count": len(fresh_findings),
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "findings": fresh_findings,
    }
