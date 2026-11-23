# InfraPilot AI — Technical Limitations & Operational Boundaries

To ensure complete transparency and engineering accuracy, this document records the architectural constraints, hardware boundaries, and technical trade-offs of InfraPilot AI v1.0.0.

---

## 1. SoloHost Sandbox Boundary vs. Host Telemetry (Mode A vs Mode B)

- **Container Cgroups**: When InfraPilot AI runs inside the isolated Pi Desktop SoloHost container environment (Mode A), `psutil` reads the container's cgroup limits rather than the physical host's full hardware state.
- **Root Protection**: SoloHost security guidelines strictly prohibit mounting `/proc`, `/sys`, or `/var/run/docker.sock` from the host.
- **Resolution**: This boundary is cleanly bridged using the companion agent (`infrapilot-agent`) or Direct SSH monitoring. Operators install `infrapilot-agent` on their physical Linux or Pi node (Mode B), which securely streams real hardware, process, and systemd telemetry into the SoloHost Control Center via authenticated REST/WebSocket endpoints.

---

## 2. Local Ollama LLM Inference on CPU

- **Hardware Acceleration**: On systems without dedicated Nvidia/CUDA or Apple Silicon neural engines, Ollama runs in CPU-only mode (AVX2/AVX-512).
- **Latency**: On an Intel 13th Gen CPU, `qwen3:4b` inference generates approximately 15-25 tokens/second. Cold-start inference or complex queries with large prompt contexts can take 5 to 15 seconds.
- **Optimization Applied**: 
  - Token cap (`num_predict: 180`).
  - Low temperature (`temperature: 0.3`).
  - Fast regex-based deterministic fallback if Ollama service is stopped or times out past 45 seconds.
  - Model thinking tags (`<think>...</think>`) are parsed and stripped so operators receive clear, actionable conclusions.

---

## 3. Safe Action Subsystem Restrictions

- **Non-Arbitrary by Design**: Operators cannot type arbitrary shell commands into the dashboard. Remediation actions are intentionally confined to the pre-compiled template catalog (`clean_docker_system`, `clean_docker_images`, `trim_system_logs`, `restart_service`, `stop_service`).
- **Target Sanitization**: Service and container targets must match `^[a-zA-Z0-9_\-\.@]{1,64}$`. Wildcard patterns or paths are rejected.
- **Time-to-Live**: Action authorization tokens expire after 300 seconds (5 minutes). If unapproved within that window, the action must be re-previewed.

---

## 4. Pi Network Payments & Mainnet Sandbox

- **Pi Payments Integration**: The Pi Network SDK and payment workflows are structured for Sandbox/Testnet verification.
- **Pi Desktop Browser Sandbox**: Production payments require the Pi Browser mobile or desktop environment with user biometric/passphrase authentication. Within pure headless server automation, mock validation flows simulate the payment lifecycle.

---

## 5. Linux Platform Specifics

- **Supported Distributions**: Ubuntu 22.04 LTS, Ubuntu 24.04 LTS, Ubuntu 26.04 LTS, Debian 12 (Bookworm), Raspberry Pi OS (64-bit).
- **Systemd Dependency**: Service inspection and service management features require `systemd`. Systems running OpenRC or SysVinit will report service discovery as unsupported.
