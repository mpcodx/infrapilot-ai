# InfraPilot AI — 3-Minute Hackathon Demo Script & Storyboard

## Demo Overview
- **Product Name**: InfraPilot AI
- **Tagline**: Your Infrastructure. One Command Center.
- **Presenter**: Lead Architect / SoloHost Developer
- **Target Audience**: Pi Network Hackathon judges, Pi SoloHost operators, self-hosted Linux developers.

---

## 10-Step Demo Sequence (Timestamped)

### 0:00 - 0:20: Opening & System Overview (Steps 1 & 2)
- **Visual**: InfraPilot AI Overview Dashboard (`http://localhost:3000`).
- **Narrator**: "Welcome to InfraPilot AI. For self-hosted operators, SoloHost users, and cluster administrators, maintaining server health and security often requires deciphering obscure logs and terminal commands. InfraPilot AI transforms complex infrastructure telemetry into clear, actionable intelligence from a single command center."
- **Action**: Point out live CPU, memory, and disk telemetry streaming in real time without synthetic or simulated numbers.

### 0:21 - 0:45: Service & Remote Server Discovery (Steps 3 & 4)
- **Visual**: Navigate to **Remote Servers** and **Services** tabs.
- **Narrator**: "InfraPilot AI connects directly to multiple remote Linux servers via authenticated SSH—without requiring an agent. It automatically discovers hardware specs, systemd services, listening ports, and Docker containers with strict host key verification."
- **Action**: Display the remote server fleet and inspect detailed processes and ports.

### 0:46 - 1:20: Defensive Security Center Audit (Step 5)
- **Visual**: Navigate to **Security Center**.
- **Narrator**: "Security in self-hosting is critical. InfraPilot AI runs automated defensive audits checking for root SSH login, inactive host firewalls, world-writable critical files, and container isolation escapes."
- **Action**: Click **Run Security Audit**. The system executes checks and highlights an exposed port or SSH risk with concrete host evidence and remediation steps.

### 1:21 - 1:55: Local Ollama AI Assistant Reasoning (Steps 6 & 7)
- **Visual**: Navigate to **AI Assistant**.
- **Narrator**: "Under the hood, InfraPilot AI connects to local Ollama running `qwen3:4b`—completely private with zero cloud API dependencies. The AI receives real multi-server telemetry context to explain anomalies in plain English."
- **Action**: Click the suggested prompt: *"Explain detected security findings and advise remediations"*. The model generates an evidence-backed explanation and copyable read-only diagnostic commands.

### 1:56 - 2:35: Safe DevOps Action Engine (Steps 8 & 9)
- **Visual**: Navigate to **Containers** tab, click **Restart** on a container.
- **Narrator**: "A core architectural rule of InfraPilot AI is that the AI never executes commands directly. All operations use strict fixed templates and require explicit operator confirmation."
- **Action**: The **Safe Action Modal** opens, displaying a sanitized command preview `$ docker restart <name>`, assessing risk as Medium, and requesting approval. Click **Approve & Execute**. The action executes with output logs streamed back.

### 2:36 - 3:00: Capacity Report & SoloHost Package (Step 10)
- **Visual**: Show **Reports** PDF download and SoloHost validator output.
- **Narrator**: "InfraPilot AI generates timestamped executive PDF reports and is fully packaged for Pi Desktop SoloHost, verified against the official SoloHost contract. InfraPilot AI: Your Infrastructure. One Command Center."
