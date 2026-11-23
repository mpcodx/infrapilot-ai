# InfraPilot AI — Environment & Repository Audit Report

**Date & Time**: 2026-11-23T10:39:15+05:30  
**Inspector**: Senior Software Architect & Security Engineer  
**Audit Status**: Verified Clean  

---

## 1. Host Operating System & Hardware

| Parameter | Observed Value | Verification Command |
|---|---|---|
| **OS Distribution** | Ubuntu 26.04.1 LTS (Resolute Raccoon) | `cat /etc/os-release` |
| **Linux Kernel** | 7.0.0-43-generic x86_64 | `uname -a` |
| **CPU Architecture** | 13th Gen Intel(R) Core(TM) i7-13620H (16 CPUs) | `lscpu` |
| **Total Memory (RAM)** | 14 GiB | `free -h` |
| **Available Memory** | ~3.3 GiB | `free -h` |
| **Swap Space** | 4.0 GiB total, 1.9 GiB used, 2.1 GiB free | `free -h` |
| **Root Filesystem** | 452G total, 183G used, 247G free (43% utilization) | `df -h /` |
| **Primary GPU** | Intel Corporation Raptor Lake-P [UHD Graphics] (rev 04) | `lspci` |

---

## 2. Runtime Runtimes & Daemons

| Runtime / Service | Version / Status | Endpoint / Port |
|---|---|---|
| **Python** | 3.14.4 | Managed virtual environment `.venv/` |
| **Node.js** | v22.22.1 | Host binary |
| **npm** | 9.2.0 | Host binary |
| **Docker Engine** | 29.9.3 | Docker socket `/var/run/docker.sock` accessible |
| **Ollama Service** | 0.40.16 (Active) | `http://127.0.0.1:11434` |
| **Installed Ollama Model** | `qwen3:4b` (2.5 GB digest `359d7dd...`) | Verified via `/api/tags` |

---

## 3. Repository Paths & Workspaces

- **Physical Directory**: `/home/dev/Music/pi`
- **Symlink Path**: `/home/dev/projects/piops-ai -> /home/dev/Music/pi`
- **Git State**: Clean commit (`994fdf4`) tracking all core application components.

---

## 4. Existing Running Services & Containers

- `secureops-postgres` (`postgres:16-alpine`, port `5432->5432`) - Verified running (preserved).
- `secureops-redis` (`redis:7-alpine`, port `6379->6379`) - Verified running (preserved).

---

## 5. SoloHost Skill & Tooling

- Official SoloHost Skill installed at `.agents/skills/solohost-package/`.
- Authoritative validation script available at `.agents/skills/solohost-package/scripts/validate_api.py`.
- Validation status: **PASS** (`deployment/solohost/` passes the authoritative schema validator).
