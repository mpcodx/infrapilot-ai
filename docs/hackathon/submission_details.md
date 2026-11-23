# InfraPilot AI — Hackathon Submission Details

## Product Overview
- **Product Name**: InfraPilot AI
- **Tagline**: Your Infrastructure. One Command Center.
- **Category**: Pi Network Developer Ecosystem / SoloHost Tools / DevOps & Infrastructure

## Value Proposition for the Pi Ecosystem
As Pi Network expands with Pi Desktop and SoloHost, non-developer pioneers run local nodes and self-hosted decentralized applications on personal hardware. Managing disk capacity, port conflicts, host firewalls, and Docker container failures is often difficult and prone to security mistakes.

InfraPilot AI bridges this gap by providing:
1. **Effortless Observability**: Live, real host metrics with zero complex Grafana/Prometheus setup.
2. **Defensive Security Guardrails**: Detects exposed database ports and unsafe permissions before attackers do.
3. **Local AI Reasoning**: Integrates local Ollama (`qwen3:4b`), providing private, offline infrastructure diagnostics.
4. **Safe Action Approvals**: Eliminates human error by enforcing explicit confirmation on all container restarts or service actions.
5. **SoloHost Contract Native**: Fully validated package conforming to Pi Desktop loopback and volume isolation specifications.
6. **Agentless SSH Remote Management**: Direct discovery and diagnostics across multiple remote nodes and VPS instances.

## Pi Network Integration
- **SDK Compatibility**: Built to interface with Pi Browser authentication and Pi Payments where applicable for enterprise agent extensions.
- **SoloHost Publishing Package**: Authoritatively verified via the official SoloHost validator with loopback binding on `127.0.0.1:19420:3000`.

## Known Limitations
1. In sandboxed SoloHost containers without an external agent, host kernel metrics reflect the container cgroup boundary. Physical host telemetry is supplied by the lightweight companion agent (Mode B).
2. Local AI inference speed is bound by host CPU/RAM capabilities.

## Privacy Policy & AI Disclosure
- **AI Assistance Disclosure**: Developed with AI-augmented software engineering practices in accordance with Pi Hackathon guidelines.
- **Zero Data Exfiltration**: System telemetry, hostnames, and process names remain strictly local. No telemetry is transmitted to external cloud providers.
