import os
import json
import datetime
from typing import Dict, Any
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors


class ReportGenerator:
    REPORTS_DIR = "./reports"

    @classmethod
    def ensure_dir(cls):
        os.makedirs(cls.REPORTS_DIR, exist_ok=True)

    @classmethod
    def generate_json_report(cls, data: Dict[str, Any]) -> str:
        cls.ensure_dir()
        ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename = f"piops_report_{ts}.json"
        path = os.path.join(cls.REPORTS_DIR, filename)

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)

        return path

    @classmethod
    def generate_pdf_report(cls, data: Dict[str, Any]) -> str:
        cls.ensure_dir()
        ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename = f"infrapilot_report_{ts}.pdf"
        path = os.path.join(cls.REPORTS_DIR, filename)

        c = canvas.Canvas(path, pagesize=letter)
        width, height = letter

        # Header
        c.setFillColor(colors.HexColor("#0f172a"))
        c.rect(0, height - 70, width, 70, fill=1, stroke=0)

        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 18)
        c.drawString(40, height - 45, "InfraPilot AI — Infrastructure Diagnostics Report")

        # Subheader
        c.setFont("Helvetica", 10)
        c.setFillColor(colors.HexColor("#94a3b8"))
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        c.drawString(40, height - 60, f"Generated at: {now_iso}")

        # Section: System Overview
        y = height - 100
        c.setFillColor(colors.HexColor("#0f172a"))
        c.setFont("Helvetica-Bold", 13)
        c.drawString(40, y, "1. Executive System Overview")
        y -= 20

        metrics = data.get("metrics", {})
        c.setFont("Helvetica", 10)
        c.drawString(50, y, f"Hostname: {metrics.get('hostname', 'N/A')}")
        y -= 15
        c.drawString(50, y, f"OS: {metrics.get('os_name', 'Linux')} | Kernel: {metrics.get('kernel_version', 'N/A')}")
        y -= 15
        c.drawString(50, y, f"CPU Usage: {metrics.get('cpu_percent', 0.0)}% ({metrics.get('cpu_count', 1)} cores)")
        y -= 15
        ram_gb = round(metrics.get('ram_total', 0) / (1024**3), 2)
        ram_used_gb = round(metrics.get('ram_used', 0) / (1024**3), 2)
        c.drawString(50, y, f"RAM: {ram_used_gb} GB / {ram_gb} GB ({metrics.get('ram_percent', 0.0)}%)")
        y -= 15
        disk_gb = round(metrics.get('disk_total', 0) / (1024**3), 2)
        disk_used_gb = round(metrics.get('disk_used', 0) / (1024**3), 2)
        c.drawString(50, y, f"Disk Space: {disk_used_gb} GB / {disk_gb} GB ({metrics.get('disk_percent', 0.0)}%)")
        y -= 30

        # Section: Security Audit Findings
        c.setFont("Helvetica-Bold", 13)
        c.drawString(40, y, "2. Defensive Security Audit Findings")
        y -= 20

        findings = data.get("findings", [])
        if not findings:
            c.setFont("Helvetica", 10)
            c.drawString(50, y, "No security findings recorded during this audit.")
            y -= 15
        else:
            for f in findings[:6]:
                c.setFont("Helvetica-Bold", 10)
                sev = f.get("severity", "Info")
                if sev in ["Critical", "High"]:
                    c.setFillColor(colors.HexColor("#dc2626"))
                elif sev == "Medium":
                    c.setFillColor(colors.HexColor("#d97706"))
                else:
                    c.setFillColor(colors.HexColor("#2563eb"))

                c.drawString(50, y, f"[{sev}] {f.get('title')}")
                y -= 14
                c.setFillColor(colors.HexColor("#334155"))
                c.setFont("Helvetica", 9)
                c.drawString(60, y, f"Component: {f.get('affected_component')}")
                y -= 14
                c.drawString(60, y, f"Recommendation: {f.get('recommended_fix')}")
                y -= 20

        # Section: Capacity Headroom
        y -= 10
        c.setFillColor(colors.HexColor("#0f172a"))
        c.setFont("Helvetica-Bold", 13)
        c.drawString(40, y, "3. Capacity & Performance Headroom")
        y -= 20

        capacity = data.get("capacity", {})
        c.setFont("Helvetica", 10)
        c.drawString(50, y, f"CPU Headroom: {capacity.get('cpu_headroom_percent', 0.0)}%")
        y -= 15
        c.drawString(50, y, f"RAM Headroom: {capacity.get('ram_headroom_percent', 0.0)}%")
        y -= 15
        c.drawString(50, y, f"Disk Headroom: {capacity.get('disk_headroom_percent', 0.0)}%")
        y -= 30

        # Footer
        c.setFont("Helvetica-Oblique", 8)
        c.setFillColor(colors.HexColor("#64748b"))
        c.drawString(40, 30, "InfraPilot AI — Your Infrastructure. One Command Center. Real metrics verified from host.")

        c.save()
        return path
