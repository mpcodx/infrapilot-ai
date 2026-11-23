# InfraPilot AI — SSH Remote Connection Troubleshooting Guide

Common issues encountered when connecting remote Linux servers via SSH and their resolution steps.

---

## 1. Authentication Failed (`Permission Denied`)

### Symptoms
- Test connection reports: `SSH authentication failed (Permission denied)`.
- Server status set to `offline` or `auth_failed`.

### Diagnostic & Fix Steps
1. **Password Authentication Disabled**: Many modern cloud VPS images (AWS EC2, DigitalOcean, Hetzner) disable password authentication by default.
   - Inspect `/etc/ssh/sshd_config` on the remote host:
     ```bash
     grep PasswordAuthentication /etc/ssh/sshd_config
     ```
   - If set to `no`, either switch to **SSH Private Key authentication** in InfraPilot AI, or enable password auth:
     ```bash
     sudo sed -i 's/PasswordAuthentication no/PasswordAuthentication yes/' /etc/ssh/sshd_config
     sudo systemctl restart ssh
     ```
2. **Root Login Prohibited**: If logging in as `root`:
   - Check `PermitRootLogin` in `/etc/ssh/sshd_config`. If set to `no` or `prohibit-password`, connect using a standard user (e.g. `ubuntu`, `debian`) instead.

---

## 2. Host Key Verification Needed / Mismatch

### Symptoms
- Status shows: `untrusted_host_key` or `MismatchedHostKeyError`.

### Explanation & Resolution
- **First Connection**: InfraPilot AI will display the server's public key fingerprint. Click **Trust Host Key** in the server details page to authorize it.
- **Server Re-installed**: If the remote server was rebuilt or its SSH keys regenerated, the fingerprint will change:
  1. Verify the new fingerprint directly on the remote server:
     ```bash
     ssh-keygen -l -f /etc/ssh/ssh_host_ed25519_key.pub
     ```
  2. In the InfraPilot AI dashboard, re-trust the updated fingerprint through the server settings page.

---

## 3. Connection Timed Out

### Symptoms
- Message: `Connection timed out after 10 seconds`.

### Diagnostic & Fix Steps
1. **Firewall Blocking Port 22**: Verify security groups or UFW:
   ```bash
   sudo ufw status
   sudo ufw allow 22/tcp
   ```
2. **Network Routing**: Ensure the remote server IP is reachable from the InfraPilot AI host:
   ```bash
   ping -c 3 REMOTE_SERVER_IP
   nc -zv REMOTE_SERVER_IP 22
   ```

---

## 4. Permission Denied for Docker or Systemctl Operations

### Symptoms
- Discovery shows 0 Docker containers or action execution returns `permission denied`.

### Resolution
Ensure the SSH monitoring user has rights to read the Docker daemon socket:
```bash
sudo usermod -aG docker infrapilot-monitor
# Re-login or restart session to apply group permissions
```
