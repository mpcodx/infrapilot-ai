# InfraPilot AI

> **Your Infrastructure. One Command Center.**

InfraPilot AI is an AI-powered infrastructure management platform that enables users to monitor, secure, analyze, and manage multiple servers through SSH connections and lightweight monitoring agents. It provides real-time infrastructure insights, service discovery, performance analysis, security auditing, AI-assisted troubleshooting, and safe approval-based operations from a centralized dashboard.

---

## Key Features

- **Agentless SSH Remote Server Management**: Connect directly to remote Linux servers and cloud VPS instances over authenticated SSH (Password or Private Key). Enforces strict host key fingerprint verification against Man-in-the-Middle (MITM) attacks.
- **Automated Deep Discovery**: Automatically discovers OS release, kernel specs, processor architecture, disk partitions, running processes, systemd services, listening network sockets, and Docker containers.
- **Defensive Security Center**: Automated audit engine checking SSH root login, password auth, host firewalls (UFW), exposed database ports, world-writable files, and container isolation.
- **Live Host Telemetry**: Hardware metrics collected via `psutil` (per-core CPU, RAM buffers, disk partitions, I/O rates, network rates, system load averages).
- **Multi-Server AI Assistant**: Contextual reasoning using local models (`qwen3:4b`), multi-server telemetry comparison, sanitized prompt injection protection, copyable commands, and deterministic rule-based fallbacks.
- **Safe DevOps Action Engine**: Strict fixed templates and argument arrays with command injection prevention, preview generation, and mandatory operator approval.
- **Pi Network SoloHost Ready**: Validated against the official SoloHost publishing contract (`127.0.0.1:19420:3000` primary UI, named volumes, no root privileges).
- **Executive Diagnostics Reporting**: Exportable timestamped PDF and JSON diagnostics reports with real measured headroom.
- **Companion Linux Agent**: Lightweight restricted agent for remote nodes communicating via authenticated HTTPS.

---

## Architecture Overview

```
infrapilot-ai/
├── backend/               # FastAPI asynchronous backend with SQLAlchemy, psutil, asyncssh
│   ├── app/
│   │   ├── api/v1/        # REST & WebSocket endpoints (System, Servers, Security, AI, etc.)
│   │   ├── monitoring/    # LinuxCollector & DiscoveryService
│   │   ├── security/      # SecurityAuditor (defensive rules)
│   │   ├── diagnostics/   # CapacityEngine (bottlenecks & headroom)
│   │   ├── ai/            # OllamaService & rule fallback
│   │   ├── services/      # SSHService, SafeActionEngine & ReportGenerator
│   │   ├── core/          # Encryption (Fernet AES-128), Database & Config
│   │   ├── workers/       # Asynchronous Remote Monitor & Polling Worker
│   │   └── websocket/     # Real-time WebSocket connection manager
│   ├── tests/             # 42 Automated tests (pytest)
│   └── Dockerfile
├── frontend/              # Next.js 14 App Router dashboard (TypeScript + Tailwind)
│   ├── app/               # 13 functional dashboard views including /servers & /servers/[id]
│   ├── components/        # Sidebar, Header, MetricCard, ActionModal
│   └── Dockerfile
├── agent/                 # Lightweight restricted monitoring agent (Mode B)
├── deployment/
│   ├── docker/            # Production compose definitions
│   └── solohost/          # Authoritatively validated SoloHost package
├── docs/                  # Architecture, SSH guides, GHCR guide, and release assets
└── scripts/               # Launch, build, and publishing scripts
```

---

## Quickstart

### 1. Local Development (Ubuntu)

```bash
# Enter directory
cd ~/projects/piops-ai # (or workspace path)

# Launch development environment (FastAPI + Next.js)
./scripts/run_dev.sh
```

- **Frontend Dashboard**: [http://localhost:3000](http://localhost:3000)
- **API Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)

### 2. Running Automated Tests

```bash
# Run backend, SSH, security, and agent pytest suite
source .venv/bin/activate
PYTHONPATH=. pytest backend/tests/ agent/tests/ -v
```

### 3. Docker Compose Deployment

```bash
docker compose up -d --build
```

### 4. SoloHost Package Validation

```bash
python3 .agents/skills/solohost-package/scripts/validate_api.py deployment/solohost
```

---

## Dual Operating & Monitoring Modes

1. **Mode A — Central Command Center**: Deployed via Docker Compose or SoloHost. Provides the unified dashboard, fleet inventory, SSH discovery, AI diagnostics, and reporting.
2. **Mode B — Companion Node Agent**: Installed directly on edge devices or restricted hosts without root access, streaming telemetry to the Central Command Center via authenticated endpoints.

---

## License

This project is licensed under the MIT License. See [LICENSE](file:///home/dev/Music/pi/LICENSE) for details.
