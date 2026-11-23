# InfraPilot AI — Remote Credential Security & Protection Architecture

**Security Level**: High / Enterprise Defense  
**Scope**: SSH Passwords, Private Keys, Passphrases, and Cryptographic Tokens

---

## 1. Zero Plaintext Storage Policy

InfraPilot AI enforces a strict zero-plaintext storage policy across all components:
1. **Never Stored in Plaintext**: Neither passwords nor private keys are ever stored unencrypted in database tables or flat files.
2. **Never Written to Logs**: All credentials and passphrases are excluded from application debug logs, audit logs, and console traces.
3. **Never Returned via API**: API responses return boolean metadata (`has_credential: true`, `has_passphrase: false`) and UI masks (`••••••••••••••••`). The raw credentials cannot be read back through REST or WebSocket endpoints.
4. **Never Sent to AI Models**: System prompts sent to local Ollama (`qwen3:4b`) or any LLM contain strictly hardware metrics, service names, and security findings. Credentials are scrubbed and never passed to AI context.

---

## 2. Cryptographic Encryption Engine (`backend/app/core/encryption.py`)

Credentials are encrypted at rest using the **Fernet symmetric encryption** specification:
- **Cipher**: AES-128 in CBC mode with PKCS7 padding.
- **Integrity**: HMAC-SHA256 authentication tag ensuring ciphertext cannot be forged or tampered with.
- **Key Derivation**: Keys are derived using PBKDF2HMAC (100,000 iterations of SHA-256) when configured via `PI_ENCRYPTION_KEY`.
- **Persistent Key Management**: If an environment key is not specified, a dedicated key file is generated at `data/.encryption_key` with strict POSIX file permissions (`0600` read/write for owner only).

---

## 3. Credential Lifecycle Management

### 3.1 Credential Rotation
Operators can rotate passwords or private keys at any time via `PUT /api/v1/servers/{server_id}` or through the Server Settings UI. New credentials immediately overwrite and re-encrypt the stored secret token.

### 3.2 Credential Revocation & Deletion
When a server registration is deleted (`DELETE /api/v1/servers/{server_id}`), the encrypted credential and passphrase are permanently purged from the database.

---

## 4. Protection Against Command Injection

When executing approved remediation operations on remote hosts:
1. **Strict Whitelist Regex**: Any target argument (such as a systemd unit name or container name) must match `^[a-zA-Z0-9_\-\.@]{1,64}$`.
2. **Rejection of Shell Operators**: Any string containing `;`, `&`, `|`, `` ` ``, `$`, `>`, `<`, or newlines is rejected with HTTP 400 before connecting to SSH.
3. **No Dynamic Shell Composition**: Commands are compiled exclusively from predefined templates (`systemctl restart <target>`, `docker stop <target>`).
