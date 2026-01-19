"""
Token encryption utilities for secure storage of OAuth tokens.
Uses Fernet symmetric encryption with the Django SECRET_KEY.
"""
import base64
import hashlib
from cryptography.fernet import Fernet
from django.conf import settings


def get_encryption_key():
    """
    Generate a Fernet-compatible key from Django's SECRET_KEY.
    The SECRET_KEY is hashed to ensure it's exactly 32 bytes (URL-safe base64).
    """
    # Use SHA256 to get 32 bytes from SECRET_KEY
    key_bytes = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
    # Fernet requires URL-safe base64 encoded 32-byte key
    return base64.urlsafe_b64encode(key_bytes)


def encrypt_token(token: str) -> str:
    """
    Encrypt a token string for secure database storage.
    Returns base64-encoded ciphertext.
    """
    if not token:
        return ""
    
    fernet = Fernet(get_encryption_key())
    encrypted = fernet.encrypt(token.encode())
    return encrypted.decode()


def decrypt_token(encrypted_token: str) -> str:
    """
    Decrypt a previously encrypted token.
    Returns the original token string.
    """
    if not encrypted_token:
        return ""
    
    try:
        fernet = Fernet(get_encryption_key())
        decrypted = fernet.decrypt(encrypted_token.encode())
        return decrypted.decode()
    except Exception:
        # If decryption fails (key changed, corrupted data), return empty
        return ""
