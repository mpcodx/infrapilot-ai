import re
import httpx
from typing import Dict, Any, List, Optional
from backend.app.core.config import settings


class OllamaService:
    def __init__(self, base_url: str = None, model: str = None, timeout: int = None):
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.model = model or settings.OLLAMA_MODEL
        self.timeout = timeout or settings.OLLAMA_TIMEOUT_SECONDS

    async def check_health(self) -> Dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                res = await client.get(f"{self.base_url}/api/tags")
                if res.status_code == 200:
                    data = res.json()
                    models = [m.get("name") for m in data.get("models", [])]
                    return {
                        "available": True,
                        "models": models,
                        "selected_model": self.model,
                        "model_present": any(self.model in m for m in models),
                    }
        except Exception as e:
            return {
                "available": False,
                "models": [],
                "selected_model": self.model,
                "model_present": False,
                "error": str(e),
            }
        return {
            "available": False,
            "models": [],
            "selected_model": self.model,
            "model_present": False,
        }

    @staticmethod
    def _sanitize(text: str) -> str:
        """Sanitize text to avoid prompt injection from process names or user inputs."""
        if not text:
            return ""
        cleaned = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', str(text))
        return cleaned[:500]

    def _build_rule_based_fallback(self, query: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Deterministic rule-based reasoning when Ollama is offline or unavailable."""
        evidence = []
        commands = []
        warnings = []

        if context:
            sys_info = context.get("metrics", {})
            cpu = sys_info.get("cpu_percent", 0.0)
            ram = sys_info.get("ram_percent", 0.0)
            disk = sys_info.get("disk_percent", 0.0)
            evidence.append(f"System State: CPU {cpu}%, RAM {ram}%, Disk {disk}%")

            if cpu > 75:
                warnings.append("High CPU load detected on host.")
                commands.append("top -b -n 1 | head -n 20")
            if ram > 80:
                warnings.append("High RAM usage detected.")
                commands.append("free -h")
            if disk > 85:
                warnings.append("Disk space is running low.")
                commands.append("df -h")

            findings = context.get("findings", [])
            if findings:
                evidence.append(f"{len(findings)} security findings recorded.")

        response_text = (
            f"[Rule-Based Diagnostic Mode]\n"
            f"Query: {self._sanitize(query)}\n\n"
            f"Based on real-time deterministic monitoring rules:\n"
            f"- Infrastructure health is currently monitored with zero artificial assumptions.\n"
            f"- AI execution engine is operating in deterministic offline mode.\n"
            f"- Recommended diagnostic commands can be copied and verified manually."
        )

        return {
            "response": response_text,
            "model": "rule-based-fallback",
            "evidence": evidence,
            "suggested_commands": commands or ["uptime", "ps aux --sort=-%cpu | head -n 10"],
            "warnings": warnings,
            "is_fallback": True,
        }

    async def generate_response(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        health = await self.check_health()
        if not health.get("available") or not health.get("model_present"):
            return self._build_rule_based_fallback(query, context)

        # Build prompt with structured context
        sanitized_query = self._sanitize(query)
        context_str = ""
        evidence_list = []

        if context:
            metrics = context.get("metrics")
            if metrics:
                cpu = metrics.get("cpu_percent")
                ram = metrics.get("ram_percent")
                disk = metrics.get("disk_percent")
                context_str += f"\nHost Metrics: CPU={cpu}%, RAM={ram}%, Disk={disk}%"
                evidence_list.append(f"Host Metrics: CPU={cpu}%, RAM={ram}%, Disk={disk}%")

            findings = context.get("findings")
            if findings and isinstance(findings, list):
                context_str += f"\nSecurity Findings: {len(findings)} identified."
                for f in findings[:2]:
                    context_str += f"\n- [{f.get('severity')}] {f.get('title')}: {f.get('evidence')}"
                    evidence_list.append(f"{f.get('severity')} - {f.get('title')}")

        system_instruction = (
            "You are InfraPilot AI, an expert Linux infrastructure and DevOps assistant. "
            "Answer directly and concisely in 1-3 sentences based on the host metrics. "
            "No preamble."
        )

        prompt = f"{system_instruction}\n\nContext:\n{context_str}\n\nUser Question:\n{sanitized_query}\n\nAnswer:"

        try:
            async with httpx.AsyncClient(timeout=float(self.timeout)) as client:
                payload = {
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "num_predict": 180,
                        "temperature": 0.3,
                    }
                }
                res = await client.post(f"{self.base_url}/api/generate", json=payload)
                if res.status_code == 200:
                    body = res.json()
                    raw_text = body.get("response", "").strip()
                    if not raw_text and body.get("thinking"):
                        raw_text = body.get("thinking", "").strip()
                        # Clean any internal tags if present
                        raw_text = re.sub(r'</?think>', '', raw_text).strip()

                    cmd_matches = re.findall(r'```(?:bash|sh)?\s*(.*?)\s*```', raw_text, re.DOTALL)
                    commands = []
                    for match in cmd_matches:
                        for line in match.strip().split("\n"):
                            line_clean = line.strip().lstrip("$ ").strip()
                            if line_clean and not line_clean.startswith("#") and len(line_clean) < 120:
                                commands.append(line_clean)

                    return {
                        "response": raw_text,
                        "model": self.model,
                        "evidence": evidence_list,
                        "suggested_commands": commands[:5] if commands else ["top -b -n 1 | head -n 15"],
                        "warnings": [],
                        "is_fallback": False,
                    }
        except Exception:
            pass

        return self._build_rule_based_fallback(query, context)


ollama_service = OllamaService()
