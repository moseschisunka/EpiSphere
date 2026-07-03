"""Privacy helpers for sensitive health identifiers."""

import hashlib
import hmac
from typing import Optional

from app.core.config import settings


def normalize_identifier(value: Optional[str]) -> Optional[str]:
    """Normalize identifiers before hashing or masked display."""
    if value is None:
        return None
    normalized = " ".join(value.strip().upper().split())
    return normalized or None


def hash_identifier(value: Optional[str]) -> Optional[str]:
    """Return a deterministic HMAC hash for duplicate detection/search."""
    normalized = normalize_identifier(value)
    if not normalized:
        return None
    return hmac.new(
        settings.SECRET_KEY.encode("utf-8"),
        normalized.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def mask_identifier(value: Optional[str]) -> Optional[str]:
    """Return a non-sensitive display value for an identifier."""
    normalized = normalize_identifier(value)
    if not normalized:
        return None
    if len(normalized) <= 4:
        return "*" * len(normalized)
    return f"***{normalized[-4:]}"
