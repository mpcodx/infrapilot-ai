import os
import stat
import uuid
import datetime
import shutil
import subprocess
from typing import List, Dict, Any

try:
    import docker
except ImportError:
    docker = None


class SecurityAuditor:
    @staticmethod
    def audit_ssh_config() -> List[Dict[str, Any]]:
        findings = []
        primary_config = "/etc/ssh/sshd_config"

        if os.path.exists(primary_config) and os.access(primary_config, os.R_OK):
            try:
                with open(primary_config, "r") as f:
                    content = f.read()

                lines = [line.strip() for line in content.splitlines() if line.strip() and not line.strip().startswith("#")]
                
                permit_root = None
                password_auth = None
                for line in lines:
                    parts = line.split()
                    if len(parts) >= 2:
                        key = parts[0].lower()
                        val = parts[1].lower()
                        if key == "permitrootlogin":
                            permit_root = val
                        elif key == "passwordauthentication":
                            password_auth = val

                if permit_root in ["yes", "without-password"]:
                    findings.append({
                        "finding_id": f"SEC-SSH-001-{uuid.uuid4().hex[:6]}",
                        "severity": "High" if permit_root == "yes" else "Medium",
                        "category": "SSH Configuration",
                        "title": "Root Login Enabled in SSH",
                        "description": "SSH daemon configuration permits root login directly.",
                        "affected_component": primary_config,
                        "evidence": f"PermitRootLogin {permit_root}",
                        "explanation": "Allowing root login over SSH increases brute-force risks against administrative credentials.",
                        "recommended_fix": "Set 'PermitRootLogin no' in /etc/ssh/sshd_config and reload sshd.",
                        "confidence": 1.0,
                    })

                if password_auth == "yes":
                    findings.append({
                        "finding_id": f"SEC-SSH-002-{uuid.uuid4().hex[:6]}",
                        "severity": "Medium",
                        "category": "SSH Configuration",
                        "title": "SSH Password Authentication Enabled",
                        "description": "SSH accepts password authentication rather than enforcing public key authentication.",
                        "affected_component": primary_config,
                        "evidence": "PasswordAuthentication yes",
                        "explanation": "Password authentication is vulnerable to credential spraying and brute force.",
                        "recommended_fix": "Deploy SSH public keys and configure 'PasswordAuthentication no'.",
                        "confidence": 1.0,
                    })
            except Exception:
                pass
        return findings

    @staticmethod
    def audit_firewall() -> List[Dict[str, Any]]:
        findings = []
        if shutil.which("ufw"):
            try:
                res = subprocess.run(["ufw", "status"], capture_output=True, text=True, timeout=2)
                if res.returncode == 0:
                    status_line = res.stdout.strip().split("\n")[0]
                    if "inactive" in status_line.lower():
                        findings.append({
                            "finding_id": f"SEC-FW-001-{uuid.uuid4().hex[:6]}",
                            "severity": "Medium",
                            "category": "Host Firewall",
                            "title": "UFW Host Firewall Inactive",
                            "description": "Uncomplicated Firewall (UFW) is installed on the host but is currently inactive.",
                            "affected_component": "ufw.service",
                            "evidence": status_line,
                            "explanation": "An inactive host firewall exposes bound listening ports directly to the local or public network.",
                            "recommended_fix": "Review allowed rules (e.g. ufw allow 22/tcp) and run 'sudo ufw enable'.",
                            "confidence": 0.95,
                        })
            except Exception:
                pass
        return findings

    @staticmethod
    def audit_listening_ports(ports: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        findings = []
        insecure_ports = {
            21: ("FTP", "Critical", "Plaintext FTP service detected."),
            23: ("Telnet", "Critical", "Unencrypted Telnet service detected."),
            6379: ("Redis", "High", "Redis database listening on non-loopback interface."),
            5432: ("PostgreSQL", "Medium", "PostgreSQL database port exposed on external interface."),
            27017: ("MongoDB", "High", "MongoDB port exposed on external interface."),
        }

        for p in ports:
            port = p.get("local_port")
            addr = p.get("local_address", "")
            is_wildcard = addr in ["0.0.0.0", "::", "*"]

            if port in insecure_ports and is_wildcard:
                svc, sev, desc = insecure_ports[port]
                findings.append({
                    "finding_id": f"SEC-NET-{port}-{uuid.uuid4().hex[:6]}",
                    "severity": sev,
                    "category": "Exposed Network Services",
                    "title": f"Potentially Dangerous Exposed Port: {svc} ({port})",
                    "description": desc,
                    "affected_component": f"{addr}:{port} ({p.get('process_name') or 'unknown'})",
                    "evidence": f"Bound to wildcard address {addr}:{port} with state {p.get('status')}",
                    "explanation": f"{svc} listening on 0.0.0.0 without localhost restriction may be reachable from untrusted networks.",
                    "recommended_fix": f"Bind {svc} to 127.0.0.1 or configure host firewall rules.",
                    "confidence": 0.9,
                })
        return findings

    @staticmethod
    def audit_file_permissions() -> List[Dict[str, Any]]:
        findings = []
        critical_files = [
            ("/etc/shadow", 0o640, "High"),
            ("/etc/passwd", 0o644, "Medium"),
            ("/etc/sudoers", 0o440, "High"),
            ("/etc/ssh/sshd_config", 0o644, "Medium"),
        ]

        for path, max_perm, sev in critical_files:
            if os.path.exists(path):
                try:
                    mode = stat.S_IMODE(os.stat(path).st_mode)
                    if mode & stat.S_IWOTH:
                        findings.append({
                            "finding_id": f"SEC-PERM-{uuid.uuid4().hex[:6]}",
                            "severity": "Critical",
                            "category": "File Permissions",
                            "title": f"World-Writable Critical File: {path}",
                            "description": f"The security-critical file {path} has world-writable permissions.",
                            "affected_component": path,
                            "evidence": f"File permission mode: {oct(mode)}",
                            "explanation": "Any local user can modify this critical system file, which can lead to complete privilege escalation.",
                            "recommended_fix": f"Remove world write access: chmod o-w {path}",
                            "confidence": 1.0,
                        })
                except PermissionError:
                    continue
        return findings

    @staticmethod
    def audit_docker() -> List[Dict[str, Any]]:
        findings = []
        if not docker:
            return findings

        try:
            client = docker.from_env(timeout=2)
            containers = client.containers.list(all=True)
            for c in containers:
                attrs = c.attrs
                host_config = attrs.get("HostConfig", {})
                
                # Check privileged mode
                if host_config.get("Privileged", False):
                    findings.append({
                        "finding_id": f"SEC-DKR-PRIV-{c.short_id}-{uuid.uuid4().hex[:6]}",
                        "severity": "Critical",
                        "category": "Container Security",
                        "title": f"Privileged Container: {c.name}",
                        "description": f"Container {c.name} is running with full host root privileges (Privileged=true).",
                        "affected_component": f"Docker container {c.name} ({c.short_id})",
                        "evidence": f"Privileged flag is true for image {c.image.tags[0] if c.image.tags else c.image.short_id}",
                        "explanation": "Privileged containers disable Docker isolation and allow container escapes to the host.",
                        "recommended_fix": "Remove 'privileged: true' and grant only specifically required capabilities.",
                        "confidence": 1.0,
                    })

                # Check sensitive host bind mounts
                binds = host_config.get("Binds") or []
                for b in binds:
                    if isinstance(b, str) and (":/host" in b or b.startswith("/:") or b.startswith("/var/run/docker.sock:")):
                        findings.append({
                            "finding_id": f"SEC-DKR-MNT-{c.short_id}-{uuid.uuid4().hex[:6]}",
                            "severity": "High",
                            "category": "Container Security",
                            "title": f"Sensitive Host Mount in Container: {c.name}",
                            "description": f"Container {c.name} mounts sensitive host paths.",
                            "affected_component": f"Docker container {c.name}",
                            "evidence": f"Mount specification: {b}",
                            "explanation": "Exposing host paths (especially docker.sock or root filesystem) enables host privilege escalation.",
                            "recommended_fix": "Remove host root and docker.sock bind mounts or use an isolated API proxy.",
                            "confidence": 1.0,
                        })
        except Exception:
            pass
        return findings

    @classmethod
    def run_full_audit(cls, ports: List[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        if ports is None:
            ports = []

        all_findings = []
        all_findings.extend(cls.audit_ssh_config())
        all_findings.extend(cls.audit_firewall())
        all_findings.extend(cls.audit_listening_ports(ports))
        all_findings.extend(cls.audit_file_permissions())
        all_findings.extend(cls.audit_docker())

        if not all_findings:
            all_findings.append({
                "finding_id": f"SEC-INFO-001-{uuid.uuid4().hex[:6]}",
                "severity": "Informational",
                "category": "Audit Summary",
                "title": "Baseline System Security Checks Passed",
                "description": "Standard SSH, file permission, and container checks identified no immediate critical vulnerabilities.",
                "affected_component": "Host System",
                "evidence": "Inspected SSH configurations, critical file permissions, and active container settings.",
                "explanation": "No critical misconfigurations detected during the automated defensive audit.",
                "recommended_fix": "Continue routine monitoring and package updates.",
                "confidence": 1.0,
            })

        now_str = datetime.datetime.now(datetime.timezone.utc).isoformat()
        for f in all_findings:
            f["timestamp"] = now_str
            f["status"] = "open"

        return all_findings
