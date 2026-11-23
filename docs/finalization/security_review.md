# InfraPilot AI — Security Architecture & Hardening Review

**Document Version**: 1.0.0  
**Security Classification**: Production Grade / Defensive  
**Target Environments**: Ubuntu Linux 24.04/26.04, Pi Desktop SoloHost, Containerized Kubernetes/Docker

---

## 1. Threat Model & Security Posture

InfraPilot AI operates at the intersection of infrastructure telemetry, local machine learning inference, and DevOps remediation. Because the software interacts with system controls, our security architecture adheres strictly to:
1. **Principle of Least Privilege (PoLP)**
2. **Deterministic Remediation Engine (Safe Action Subsystem)**
3. **No Unrestricted Host Access inside Sandboxed Runtimes**
4. **Boundary Defense Between Local Telemetry and Remote Orchestration**

---

## 2. Safe DevOps Action Engine: Defenses Against Arbitrary Execution

### 2.1 The Problem
Traditional AI DevOps tools allow large language models to emit raw shell strings (`rm`, `kill`, `docker rm`) that are executed via a root shell (`/bin/sh -c`). This exposes the system to prompt injection, hallucinated dangerous flags (`-rf /`), and command chaining exploits (`;`, `&&`, `|`, `$(...)`).

### 2.2 Our Hardened Architecture
In InfraPilot AI, neither the user nor the AI can submit arbitrary commands.
- **Fixed Action Catalog**: Only pre-compiled, vetted action templates can be executed:
  - `clean_docker_system`: Invokes `['docker', 'system', 'prune', '-f']`.
  - `clean_docker_images`: Invokes `['docker', 'image', 'prune', '-a', '-f']`.
  - `trim_system_logs`: Invokes `['journalctl', '--vacuum-size=200M']`.
  - `restart_service`: Invokes `['systemctl', 'restart', <target>]`.
  - `stop_service`: Invokes `['systemctl', 'stop', <target>]`.
- **Target Sanitization**: Any parameter (such as a systemd service name) is validated against a strict alphanumeric whitelist regex: `^[a-zA-Z0-9_\-\.@]{1,64}$`. Any semicolons, null bytes, backticks, or spaces cause immediate rejection (HTTP 400).
- **Execution Vector**: Commands are executed using Python's `subprocess.run(command_list, shell=False, check=False)`. Bypassing shell parsing guarantees that shell injection is impossible.
- **Two-Phase Approval Workflow**:
  1. An action must first be **previewed** (`POST /api/v1/actions/preview`). The engine validates parameters, assigns a cryptographic UUIDv4 token, and sets a 5-minute time-to-live (`expires_at`).
  2. The action can only run when an operator explicitly invokes `POST /api/v1/actions/approve` with the valid token.
  3. The token is immediately marked `executed` in the database, preventing replay attacks. Expired tokens are rejected.

---

## 3. Ollama Prompt Injection Defense & Privacy

- **Local Inference Guarantee**: All prompts are sent exclusively to local or private Ollama instances (`http://127.0.0.1:11434` or user-defined private endpoint). No metric data, host details, or logs ever leave the local network.
- **System Prompt Integrity**: Prompts are structured with strict system boundaries:
  - System instructions enforce that the model is a read-only diagnostics advisor.
  - The model is instructed to recommend actions by template name only, never as shell commands.
- **Input Sanitization**: User and event text is sanitized by stripping common override keywords (`IGNORE ALL PREVIOUS INSTRUCTIONS`, `SYSTEM OVERRIDE`, `<script>`) before passing to Ollama.
- **Timeout & Resource Limiting**: HTTP requests to Ollama are capped at 45 seconds with token limits (`num_predict: 180`) and low sampling temperature (`temperature: 0.3`) to prevent CPU exhaustion on host systems.

---

## 4. SoloHost Container Isolation & Sandbox Compliance

Pi Desktop SoloHost packages run in an isolated Docker bridge network. InfraPilot AI respects these platform isolation guarantees:
1. **No Host Bind Mounts**: Does not mount `/`, `/proc`, `/sys`, or the host `/var/run/docker.sock` inside the SoloHost package.
2. **No Privileged Flags**: Containers run unprivileged (`privileged: false` by default).
3. **Dedicated Loopback Port**: Primary web UI binds strictly to `127.0.0.1:19420` to eliminate unauthorized local network access.
4. **Companion Agent Architecture**: When running inside SoloHost (Mode A - Control Center), the application relies on the lightweight companion agent (`infrapilot-agent`) deployed on physical target nodes to stream host metrics via authenticated HTTP tokens.

---

## 5. Defensive Security Auditor Capabilities

The built-in defensive security auditor (`auditor.py`) performs non-destructive, read-only security checks:
- **SSH Hardening**: Verifies `/etc/ssh/sshd_config` or `/etc/ssh/sshd_config.d/` for `PermitRootLogin no` and `PasswordAuthentication no`.
- **Host Firewall Status**: Inspects `ufw status` to confirm active firewall defense.
- **Public Port Exposure**: Correlates listening sockets with `0.0.0.0` or `::` bindings to warn operators of publicly reachable database or cache ports.
- **Critical File Permissions**: Audits permissions on `/etc/shadow` and `/etc/passwd`.
- **Container Privilege Verification**: Scans running Docker containers for dangerous privileged runtime flags or host root volume mappings.

---

## 6. Audit Trail & Incident Logging

Every action previewed, approved, or executed is persisted in the SQLite audit log with:
- Client IP address.
- Timestamp in UTC ISO 8601 format.
- Action template name and target parameters.
- Exit code and stdout/stderr results.
- Approval status and execution latency.
