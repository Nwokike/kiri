"""
Token encryption utilities for secure storage of OAuth tokens.
Uses Fernet symmetric encryption with a dedicated ENCRYPTION_KEY,
falling back to SECRET_KEY if not set.

IMPORTANT: If ENCRYPTION_KEY or SECRET_KEY changes, all stored
encrypted tokens become permanently unreadable. Users will need
to re-authenticate via OAuth to generate new tokens.
"""
import base64
import hashlib
import os
from cryptography.fernet import Fernet
from django.conf import settings


def get_encryption_key():
    """
    Generate a Fernet-compatible key from ENCRYPTION_KEY env var.
    Falls back to SECRET_KEY if ENCRYPTION_KEY is not set.
    """
    key_source = os.environ.get('ENCRYPTION_KEY', '') or str(settings.SECRET_KEY)
    key_bytes = hashlib.sha256(key_source.encode()).digest()
    return base64.urlsafe_b64encode(key_bytes)


def encrypt_token(token: str) -> str:
    """Encrypt a token string for secure database storage."""
    if not token:
        return ""
    fernet = Fernet(get_encryption_key())
    encrypted = fernet.encrypt(token.encode())
    return encrypted.decode()


def decrypt_token(encrypted_token: str) -> str:
    """Decrypt a previously encrypted token."""
    if not encrypted_token:
        return ""
    try:
        fernet = Fernet(get_encryption_key())
        decrypted = fernet.decrypt(encrypted_token.encode())
        return decrypted.decode()
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Token decryption failed: {e}")
        return ""
