"""
Security utilities: JWT, password hashing, authentication
"""

from datetime import datetime, timedelta
from typing import Optional
import bcrypt
import base64
import hashlib
import hmac
import secrets
import jwt
from jwt.exceptions import PyJWTError
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


def get_password_hash(password: str) -> str:
    """Hash a password"""
    return bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt(),
    ).decode("utf-8")


def generate_opaque_token() -> str:
    """Generate a high-entropy one-time token for account workflows."""
    return secrets.token_urlsafe(32)


def hash_security_token(token: str) -> str:
    return hmac.new(
        settings.SECRET_KEY.encode("utf-8"),
        token.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def generate_totp_secret() -> str:
    return base64.b32encode(secrets.token_bytes(20)).decode("ascii").rstrip("=")


def generate_totp_code(secret: str, timestamp: Optional[datetime] = None) -> str:
    """Generate a 6-digit RFC 6238-compatible SHA-1 TOTP code."""
    now = timestamp or datetime.utcnow()
    counter = int(now.timestamp()) // 30
    padded_secret = secret + "=" * (-len(secret) % 8)
    key = base64.b32decode(padded_secret, casefold=True)
    digest = hmac.new(key, counter.to_bytes(8, "big"), hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    binary = int.from_bytes(digest[offset:offset + 4], "big") & 0x7FFFFFFF
    return f"{binary % 1_000_000:06d}"


def verify_totp_code(secret: str, code: str, timestamp: Optional[datetime] = None) -> bool:
    if not code or len(code) != 6 or not code.isdigit():
        return False
    now = timestamp or datetime.utcnow()
    for offset in (-1, 0, 1):
        candidate_time = now + timedelta(seconds=offset * 30)
        if hmac.compare_digest(generate_totp_code(secret, candidate_time), code):
            return True
    return False


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_mfa_challenge_token(data: dict, expires_delta: timedelta) -> str:
    """Create a JWT that can only be exchanged for an MFA-verified access token."""
    challenge_data = data.copy()
    challenge_data["token_type"] = "mfa_challenge"
    return create_access_token(challenge_data, expires_delta=expires_delta)


def decode_access_token(token: str) -> Optional[dict]:
    """Decode and verify a JWT token"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except PyJWTError:
        return None


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    """Dependency to get current authenticated user"""
    from app.db.models import User

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_access_token(token)
    if payload is None or payload.get("token_type") == "mfa_challenge":
        raise credentials_exception

    user_id = payload.get("sub")
    if user_id is None:
        raise credentials_exception
    try:
        user_id = int(user_id)
    except (TypeError, ValueError):
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception

    token_version = payload.get("ver")
    if token_version is not None and token_version != (user.token_version or 0):
        raise credentials_exception

    return user
