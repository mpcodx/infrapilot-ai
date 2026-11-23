import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from backend.app.schemas.schemas import ReportGenerateRequest
from backend.app.services.report_generator import ReportGenerator
from backend.app.monitoring.linux_collector import LinuxCollector
from backend.app.monitoring.discovery import DiscoveryService
from backend.app.security.auditor import SecurityAuditor
from backend.app.diagnostics.capacity import CapacityEngine

router = APIRouter()


@router.get("/reports")
def list_reports():
    ReportGenerator.ensure_dir()
    files = []
    for f in os.listdir(ReportGenerator.REPORTS_DIR):
        fpath = os.path.join(ReportGenerator.REPORTS_DIR, f)
        if os.path.isfile(fpath) and (f.endswith(".pdf") or f.endswith(".json")):
            stat = os.stat(fpath)
            files.append({
                "filename": f,
                "size_bytes": stat.st_size,
                "created_at": stat.st_ctime,
                "format": "pdf" if f.endswith(".pdf") else "json",
            })
    files.sort(key=lambda x: x["created_at"], reverse=True)
    return files


@router.post("/reports/generate")
def generate_report(req: ReportGenerateRequest):
    metrics = LinuxCollector.collect_full_metrics()
    ports = DiscoveryService.get_ports()
    findings = SecurityAuditor.run_full_audit(ports=ports)
    processes = DiscoveryService.get_processes(limit=10)
    containers = DiscoveryService.get_containers()
    capacity = CapacityEngine.analyze(metrics=metrics, processes=processes, containers=containers)

    report_data = {
        "metrics": metrics,
        "findings": findings,
        "capacity": capacity,
        "processes_count": len(processes),
        "containers_count": len(containers),
    }

    if req.format.lower() == "pdf":
        path = ReportGenerator.generate_pdf_report(report_data)
    else:
        path = ReportGenerator.generate_json_report(report_data)

    return {
        "status": "success",
        "format": req.format.lower(),
        "filename": os.path.basename(path),
        "download_url": f"/api/v1/reports/download/{os.path.basename(path)}",
    }


@router.get("/reports/download/{filename}")
def download_report(filename: str):
    # Prevent directory traversal
    clean_filename = os.path.basename(filename)
    path = os.path.join(ReportGenerator.REPORTS_DIR, clean_filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Report file not found.")

    media_type = "application/pdf" if clean_filename.endswith(".pdf") else "application/json"
    return FileResponse(path, media_type=media_type, filename=clean_filename)
