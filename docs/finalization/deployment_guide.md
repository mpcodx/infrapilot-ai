# InfraPilot AI — Deployment & Operations Guide

This guide details the supported deployment modes for InfraPilot AI across local development, standalone host setups, Docker Compose, and Pi Desktop SoloHost.

---

## 1. Supported Architecture Modes

InfraPilot AI supports two complementary operating modes:

```
+-----------------------------------------------------------------------------------+
| MODE A: SoloHost Containerized Control Center                                     |
|                                                                                   |
|  +------------------+         +-------------------+         +------------------+  |
|  | Next.js Frontend | <-----> |  FastAPI Backend  | <-----> |   Local Ollama   |  |
|  |  (127.0.0.1:19420)         |  (Port 8000)      |         |  (qwen3:4b)      |  |
|  +------------------+         +---------^---------+         +------------------+  |
|                                         |                                         |
|                                         | HTTP /ws                                |
|                                         v                                         |
+-----------------------------------------+-----------------------------------------+
                                          |
                      +-------------------+-------------------+
                      |                                       |
                      v                                       v
+------------------------------------+   +------------------------------------+
| MODE B: Physical Linux Host (Node) |   | Physical Linux Server / Pi (Node)  |
| +--------------------------------+ |   | +--------------------------------+ |
| | infrapilot-agent daemon        | |   | | infrapilot-agent daemon        | |
| | (Direct psutil, systemd, logs) | |   | | (Direct psutil, systemd, logs) | |
| +--------------------------------+ |   | +--------------------------------+ |
+------------------------------------+   +------------------------------------+
```

- **Mode A (SoloHost / Containerized Control Center)**: Provides the interactive UI, incident tracking, AI diagnostics, and reporting. Deployed via Docker Compose inside Pi Desktop SoloHost.
- **Mode B (Host Direct / Companion Agent)**: Runs directly on the target physical Ubuntu/Debian/Pi server. Collects granular system metrics, per-core CPU, memory pressure, and service status, streaming them to the Control Center.

---

## 2. Option 1: Pi Desktop SoloHost Installation

SoloHost allows 1-click installation of verified community applications onto Pi Desktop.

### Directory Structure
```
deployment/solohost/
├── docker-compose.yml
└── config_options.yml
```

### SoloHost Configuration Parameters
| Parameter | Default | Description |
|---|---|---|
| `APP_TITLE` | `InfraPilot AI` | Display name in Pi Desktop |
| `PI_PORT` | `19420` | Loopback binding port for the web dashboard |
| `OLLAMA_BASE_URL` | `http://host.docker.internal:11434` | Endpoint for the host Ollama runtime |
| `AI_MODEL` | `qwen3:4b` | Ollama model tag for inference |

### Validating the SoloHost Package
Run the authoritative SoloHost package validator:
```bash
python3 .agents/skills/solohost-package/scripts/validate_api.py deployment/solohost
```

---

## 3. Option 2: Docker Compose (Local / Private Server)

For standard Docker environments with local access:

```bash
# Clone the repository
git clone https://github.com/pi-node/infrapilot-ai.git
cd infrapilot-ai

# Configure environment
cp .env.example .env

# Launch the stack
docker compose up -d

# Access the interface
open http://localhost:3000
```

---

## 4. Option 3: Local Host Bare-Metal Development

### 4.1 Backend Setup
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run database migrations and start server
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### 4.2 Frontend Setup
```bash
cd frontend
npm install
npm run dev
# Dashboard available at http://localhost:3000
```

### 4.3 Companion Agent Setup
```bash
cd agent
pip install -e .
python -m piops_agent.client --server http://127.0.0.1:8000 --interval 5
```

---

## 5. Publishing Docker Images to GHCR

InfraPilot AI images are published to the GitHub Container Registry (`ghcr.io`):

```bash
# 1. Log in to GitHub Container Registry
echo $CR_PAT | docker login ghcr.io -u YOUR_GITHUB_USER --password-stdin

# 2. Build multi-arch or host images
docker build -t ghcr.io/pi-node/infrapilot-ai-api:1.0.0 ./backend
docker build -t ghcr.io/pi-node/infrapilot-ai:1.0.0 ./frontend

# 3. Push to GHCR
docker push ghcr.io/pi-node/infrapilot-ai-api:1.0.0
docker push ghcr.io/pi-node/infrapilot-ai:1.0.0
```
