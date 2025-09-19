"""Secure token storage with encryption."""

import base64
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes

from ..exceptions import TokenError

logger = logging.getLogger(__name__)


class SecureTokenStore:
    """
    Secure storage for sensitive tokens with encryption.

    This store provides:
    - Encryption at rest using Fernet (AES-128)
    - Key derivation from environment variable or auto-generated
    - File-based storage with atomic writes
    - Memory caching for performance
    - Automatic cleanup of expired tokens

    For production use, consider using a proper secrets manager
    like AWS Secrets Manager, HashiCorp Vault, or Azure Key Vault.
    """

    def __init__(
        self,
        storage_path: Optional[Path] = None,
        encryption_key: Optional[str] = None,
    ):
        """
        Initialize secure token store.

        Args:
            storage_path: Path for encrypted token storage
            encryption_key: Base64-encoded encryption key or password
        """
        self.storage_path = storage_path or self._get_default_path()
        self._fernet = self._initialize_encryption(encryption_key)
        self._memory_cache: Dict[str, Dict[str, Any]] = {}
        self._load_tokens()

    def _get_default_path(self) -> Path:
        """Get default storage path."""
        # Use XDG_DATA_HOME on Linux/Mac, APPDATA on Windows
        if os.name == "nt":  # Windows
            base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
        else:  # Unix-like
            base = Path(
                os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share")
            )

        path = base / "amazon-ads-mcp" / "tokens.enc"
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    def _initialize_encryption(self, key_input: Optional[str]) -> Fernet:
        """
        Initialize encryption with key derivation.

        Args:
            key_input: Base64 key or password to derive key from

        Returns:
            Fernet encryption instance
        """
        if not key_input:
            # Try universal environment variable
            key_input = os.getenv("AMAZON_ADS_ENCRYPTION_KEY")

        if not key_input:
            # Generate and store a key if none exists
            key_file = self.storage_path.parent / ".key"
            if key_file.exists():
                try:
                    with open(key_file, "rb") as f:
                        key = f.read()
                except Exception as e:
                    logger.warning(f"Could not read encryption key: {e}")
                    key = Fernet.generate_key()
            else:
                key = Fernet.generate_key()
                try:
                    # Save key with restricted permissions
                    with open(key_file, "wb") as f:
                        f.write(key)
                    os.chmod(key_file, 0o600)  # Owner read/write only
                except Exception as e:
                    logger.warning(f"Could not save encryption key: {e}")
        else:
            # Derive key from password if not base64
            try:
                # Try to decode as base64 first
                key = base64.urlsafe_b64decode(key_input)
                if len(key) != 32:
                    raise ValueError("Invalid key length")
            except Exception:
                # Not base64, derive key from password
                from cryptography.hazmat.primitives.kdf.pbkdf2 import (
                    PBKDF2HMAC,
                )

                kdf = PBKDF2HMAC(
                    algorithm=hashes.SHA256(),
                    length=32,
                    salt=b"amazon-ads-mcp-salt",  # Fixed salt for deterministic key
                    iterations=100000,
                    backend=default_backend(),
                )
                key = base64.urlsafe_b64encode(kdf.derive(key_input.encode()))

        return Fernet(key)

    def store_token(
        self,
        token_id: str,
        token_value: str,
        token_type: str = "refresh",
        expires_at: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Store an encrypted token.

        Args:
            token_id: Unique identifier for the token
            token_value: The sensitive token value
            token_type: Type of token (refresh, access, etc.)
            expires_at: Optional expiration time
            metadata: Optional metadata to store with token
        """
        # Prepare token entry
        entry = {
            "id": token_id,
            "type": token_type,
            "value": token_value,
            "stored_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": expires_at.isoformat() if expires_at else None,
            "metadata": metadata or {},
        }

        # Encrypt the token value
        encrypted_value = self._fernet.encrypt(token_value.encode()).decode()
        entry["value"] = encrypted_value

        # Store in memory cache (unencrypted for performance)
        self._memory_cache[token_id] = {
            **entry,
            "value": token_value,  # Keep unencrypted in memory
        }

        # Persist to disk
        self._save_tokens()

        logger.debug(f"Stored {token_type} token: {token_id}")

    def get_token(self, token_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a token by ID.

        Args:
            token_id: The token identifier

        Returns:
            Token entry with decrypted value, or None if not found/expired
        """
        # Check memory cache first
        if token_id in self._memory_cache:
            entry = self._memory_cache[token_id]
            if self._is_expired(entry):
                del self._memory_cache[token_id]
                self._save_tokens()
                return None
            return entry

        # Not in cache, shouldn't happen but handle gracefully
        self._load_tokens()
        return self._memory_cache.get(token_id)

    def delete_token(self, token_id: str):
        """Delete a token."""
        if token_id in self._memory_cache:
            del self._memory_cache[token_id]
            self._save_tokens()
            logger.debug(f"Deleted token: {token_id}")

    def clear_all(self):
        """Clear all stored tokens."""
        self._memory_cache.clear()
        if self.storage_path.exists():
            self.storage_path.unlink()
        logger.info("Cleared all tokens")

    def _is_expired(self, entry: Dict[str, Any]) -> bool:
        """Check if a token entry is expired."""
        if not entry.get("expires_at"):
            return False

        try:
            expires_at = datetime.fromisoformat(entry["expires_at"])
            return datetime.now(timezone.utc) > expires_at
        except Exception:
            return False

    def _save_tokens(self):
        """Save tokens to encrypted storage."""
        try:
            # Prepare data for storage (with encrypted values)
            storage_data = {}
            for token_id, entry in self._memory_cache.items():
                # Skip expired tokens
                if self._is_expired(entry):
                    continue

                # Encrypt the value for storage
                encrypted_entry = entry.copy()
                encrypted_entry["value"] = self._fernet.encrypt(
                    entry["value"].encode()
                ).decode()
                storage_data[token_id] = encrypted_entry

            # Serialize and encrypt entire file
            json_data = json.dumps(storage_data, indent=2)
            encrypted_data = self._fernet.encrypt(json_data.encode())

            # Atomic write
            tmp_path = self.storage_path.with_suffix(".tmp")
            with open(tmp_path, "wb") as f:
                f.write(encrypted_data)

            # Set restrictive permissions
            os.chmod(tmp_path, 0o600)

            # Atomic replace
            tmp_path.replace(self.storage_path)

        except Exception as e:
            logger.error(f"Failed to save tokens: {e}")
            raise TokenError(f"Failed to save tokens: {e}")

    def _load_tokens(self):
        """Load tokens from encrypted storage."""
        if not self.storage_path.exists():
            return

        try:
            # Read and decrypt file
            with open(self.storage_path, "rb") as f:
                encrypted_data = f.read()

            decrypted_data = self._fernet.decrypt(encrypted_data)
            storage_data = json.loads(decrypted_data)

            # Load into memory cache with decrypted values
            self._memory_cache.clear()
            for token_id, entry in storage_data.items():
                # Skip expired tokens
                if self._is_expired(entry):
                    continue

                # Decrypt the token value
                encrypted_value = entry["value"]
                decrypted_value = self._fernet.decrypt(
                    encrypted_value.encode()
                ).decode()
                entry["value"] = decrypted_value

                self._memory_cache[token_id] = entry

            logger.debug(f"Loaded {len(self._memory_cache)} tokens")

        except Exception as e:
            logger.warning(f"Could not load tokens: {e}")
            # Don't fail, just start fresh
            self._memory_cache.clear()


# Global instance
_secure_token_store: Optional[SecureTokenStore] = None


def get_secure_token_store() -> SecureTokenStore:
    """Get or create the global secure token store."""
    global _secure_token_store
    if _secure_token_store is None:
        encryption_key = os.getenv("AMAZON_ADS_ENCRYPTION_KEY")
        _secure_token_store = SecureTokenStore(encryption_key=encryption_key)
    return _secure_token_store
