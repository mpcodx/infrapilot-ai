import os
import base64
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from backend.app.core.config import settings

KEY_FILE = Path("./data/.encryption_key")


def _get_or_create_key() -> bytes:
    """Retrieve or generate a secure AES-128 Fernet key.
    
    1. Checks settings.SECRET_KEY or PI_ENCRYPTION_KEY environment variable.
    2. Otherwise checks or creates a local secure key file in data/.encryption_key.
    """
    env_key = os.getenv("PI_ENCRYPTION_KEY")
    if env_key:
        # Derive a 32-byte url-safe base64 key from env
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b"piops_ssh_salt_v1",
            iterations=100000,
        )
        return base64.urlsafe_b64encode(kdf.derive(env_key.encode()))

    # File-based persistent key
    if KEY_FILE.exists():
        try:
            with open(KEY_FILE, "rb") as f:
                return f.read().strip()
        except Exception:
            pass

    KEY_FILE.parent.mkdir(parents=True, exist_ok=True)
    new_key = Fernet.generate_key()
    try:
        with open(KEY_FILE, "wb") as f:
            f.write(new_key)
        # Ensure strict file permissions on unix
        os.chmod(KEY_FILE, 0o600)
    except Exception:
        pass
    return new_key


_fernet_instance = None


def get_fernet() -> Fernet:
    global _fernet_instance
    if _fernet_instance is None:
        _fernet_instance = Fernet(_get_or_create_key())
    return _fernet_instance


def encrypt_secret(plaintext: str) -> str:
    """Encrypt a secret string into a base64 ciphertext token."""
    if not plaintext:
        return ""
    fernet = get_fernet()
    return fernet.encrypt(plaintext.encode("utf-8")).decode("utf-8")


def decrypt_secret(ciphertext: str) -> str:
    """Decrypt a base64 ciphertext token back into plaintext."""
    if not ciphertext:
        return ""
    fernet = get_fernet()
    try:
        return fernet.decrypt(ciphertext.encode("utf-8")).decode("utf-8")
    except Exception as e:
        raise ValueError(f"Failed to decrypt credential: {str(e)}")


def mask_credential(val: str) -> str:
    """Return a masked representation for UI and log safety."""
    if not val:
        return ""
    return "••••••••••••••••"
