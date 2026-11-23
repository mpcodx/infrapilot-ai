# InfraPilot AI — Remote Server SSH Setup & Configuration Guide

**Version**: 1.0.0  
**Feature**: Direct Agentless SSH Remote Server Connection  
**Target Environments**: Ubuntu, Debian, CentOS/RHEL, Fedora, Raspberry Pi OS, Alpine Linux

---

## 1. Overview & Architectural Dual-Mode

InfraPilot AI supports two complementary connection methods for managing remote Linux servers:

| Feature | Method 1: Direct SSH Connection (Agentless) | Method 2: Companion Node Agent (`infrapilot-agent`) |
|---|---|---|
| **Installation** | **Zero installation** on remote machine | Lightweight Python daemon installed on node |
| **Authentication** | SSH Password or OpenSSH/RSA/Ed25519 Private Key | Pre-shared HMAC API token |
| **Network Direction** | Inbound from InfraPilot Control Center to Server Port 22 | Outbound HTTP/WS from node to Control Center |
| **Ideal For** | Cloud VPS, bare-metal servers, staging/prod clusters | Dynamic IP nodes, isolated home networks, firewalled Pis |
| **Operations** | Two-phase approved remote actions over SSH | Local remediation commands via agent |

---

## 2. Remote Server Prerequisites for SSH Direct

To enable InfraPilot AI to inspect and monitor a remote Linux host via SSH:

### 2.1 SSH Daemon
Ensure OpenSSH server is running and listening on port 22 (or a custom port):
```bash
sudo systemctl enable --now ssh   # On Ubuntu / Debian
# Or
sudo systemctl enable --now sshd  # On CentOS / RHEL / Fedora
```

### 2.2 Dedicated Monitoring User (Recommended)
While connecting as `root` is supported, following the Principle of Least Privilege is best practice:
```bash
# 1. Create a dedicated monitoring user
sudo useradd -m -s /bin/bash infrapilot-monitor

# 2. Add to docker or systemd groups if container monitoring is required
sudo usermod -aG docker infrapilot-monitor
```

### 2.3 SSH Key Authentication Setup (Recommended)
If using SSH Private Key authentication:
```bash
# On your operator machine, generate an Ed25519 key pair
ssh-keygen -t ed25519 -C "infrapilot-monitor@infrapilot.local" -f ~/.ssh/infrapilot_id_ed25519

# Copy the public key to the remote server
ssh-copy-id -i ~/.ssh/infrapilot_id_ed25519.pub infrapilot-monitor@REMOTE_SERVER_IP
```
Then paste the contents of `~/.ssh/infrapilot_id_ed25519` into the InfraPilot AI Add Server form.

---

## 3. Registering a Server via InfraPilot Dashboard

1. Navigate to **Remote Servers** (`/servers`) in the sidebar.
2. Click **Add Server**.
3. Fill in the connection form:
   - **Server Display Name**: e.g., `EU-Prod-App01`
   - **Hostname or IP**: e.g., `192.168.1.150` or `app.example.com`
   - **SSH Port**: `22` (or your hardened custom port)
   - **Username**: `infrapilot-monitor` or `root`
   - **Auth Method**: Choose **SSH Password** or **SSH Private Key**
   - **Credentials**: Input is immediately encrypted in memory with Fernet before database persistence.
   - **Environment**: `production`, `staging`, or `development`
4. Click **Test SSH Connection**:
   - InfraPilot AI probes the server, computes latency, and presents the observed **Host Key Fingerprint**.
   - Review and accept host key fingerprint trust.
5. Click **Save & Connect Server**.

---

## 4. SSH Host Key Verification Lifecycle

To prevent Man-in-the-Middle (MITM) attacks, InfraPilot AI strictly enforces host key verification:
1. **First Connection**: Captures the SHA256 host key fingerprint (e.g. `SHA256:abc...`). If auto-trust was not enabled, the server is placed in `untrusted_host_key` status until explicitly approved by the operator.
2. **Subsequent Polls**: Every automated poll verifies that the remote server's host key matches the trusted fingerprint.
3. **Mismatched Keys**: If a server's host key changes unexpectedly, InfraPilot AI immediately terminates the connection and raises `MismatchedHostKeyError`.
