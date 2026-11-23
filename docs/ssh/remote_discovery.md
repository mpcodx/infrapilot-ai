# InfraPilot AI — Remote Server Discovery & Diagnostic Specifications

This document outlines the read-only commands executed by InfraPilot AI during automatic server discovery over authenticated SSH sessions.

---

## 1. Discovery Architecture

During discovery, InfraPilot AI establishes a secure SSH channel and executes a bounded sequence of read-only diagnostic commands. Output is streamed directly into structured JSON parsers.

```
+------------------+         SSH Session (Port 22)         +--------------------+
| InfraPilot       | ─────────────────────────────────────> | Target Remote Node |
| Command Center   | <───────────────────────────────────── | Linux Server / Pi  |
+------------------+     Structured Standard Output         +--------------------+
```

---

## 2. Collected Diagnostic Parameters

| Category | Diagnostic Command Executed | Extracted Attributes |
|---|---|---|
| **OS & Kernel** | `uname -s -r -m -n && cat /etc/os-release` | Distribution (`PRETTY_NAME`), Version, Kernel release, Architecture (`x86_64`, `aarch64`), Hostname |
| **System Uptime** | `cat /proc/uptime` | Uptime in seconds |
| **CPU Profile** | `nproc` & `cat /proc/cpuinfo \| grep 'model name'` | Total core count, CPU model name |
| **Load Averages**| `cat /proc/loadavg` | 1-min, 5-min, 15-min load averages |
| **Memory & Swap**| `free -b` | Total, used, available physical RAM and swap in bytes |
| **Storage & Mounts** | `df -B1 -P` | Filesystem devices, mountpoints, total capacity, used bytes, free bytes, percentage |
| **Network I/O** | `cat /proc/net/dev` | Network interfaces (`eth0`, `wlan0`), RX bytes, TX bytes |
| **Running Tasks**| `ps -eo pid,user,%cpu,%mem,comm --sort=-%cpu \| head -n 26` | Top 25 processes sorted by CPU utilization, usernames, PIDs |
| **Systemd Units**| `systemctl list-units --type=service --all --no-pager --no-legend` | Loaded services, active status (`active`/`failed`), sub-states, descriptions |
| **Listening Sockets** | `ss -tuln \|\| netstat -tuln` | Protocols (TCP/UDP), local listening addresses, bind ports |
| **Containers** | `docker ps -a --format '{{.ID}}\t{{.Names}}\t{{.Image}}\t{{.Status}}\t{{.State}}'` | Running Docker containers, images, states, uptime |
| **Defensive Security**| `cat /etc/ssh/sshd_config`, `ufw status`, `ls -l /etc/shadow` | SSH root login allowance, firewall active state, shadow permissions |

---

## 3. Resilience & Missing Tool Handling

Remote servers may run minimal Linux installations (e.g. Alpine Linux, container hosts) where specific tools like `systemctl`, `ufw`, or `docker` are not present:
- **Existence Checks**: Commands append `2>/dev/null || true` to prevent non-zero return codes from aborting the SSH session.
- **Graceful Fallbacks**: If `systemctl` is unavailable, service inspection returns an empty list without raising fatal exceptions.
- **Bounded Execution**: Each command is bounded by a 15-second timeout to prevent hanging on unresponsive remote devices.
