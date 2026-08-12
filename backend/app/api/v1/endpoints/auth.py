"""Authentication endpoints"""

from datetime import datetime, timedelta
from urllib.parse import quote
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.limiter import limiter
from app.core.security import (
    create_access_token,
    create_mfa_challenge_token,
    decode_access_token,
    generate_opaque_token,
    generate_totp_secret,
    get_password_hash,
    hash_security_token,
    verify_password,
    verify_totp_code,
)
from app.core.config import settings
from app.core.dependencies import get_current_active_user, require_role
from app.db.models import User, Role, AuditLog, AuditAction, UserSecurityToken
from app.schemas.user import (
    MfaCodeRequest,
    MfaSetupResponse,
    MfaVerifyRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    Token,
    UserCreate,
    UserResponse,
    VerifyEmailRequest,
)
from app.services.auth_email_service import AuthEmailService

router = APIRouter()

SELF_REGISTRATION_ROLE = "public"
EMAIL_VERIFICATION_TOKEN = "email_verification"
PASSWORD_RESET_TOKEN = "password_reset"
PRIVILEGED_ROLES = {"admin", "epidemiologist", "country_data_officer", "facility_admin"}


def _issue_security_token(db: Session, user: User, token_type: str) -> str:
    raw_token = generate_opaque_token()
    db.add(UserSecurityToken(
        user_id=user.id,
        token_hash=hash_security_token(raw_token),
        token_type=token_type,
        expires_at=datetime.utcnow() + timedelta(minutes=settings.AUTH_TOKEN_EXPIRE_MINUTES),
    ))
    return raw_token


def _consume_security_token(db: Session, raw_token: str, token_type: str) -> User:
    token = db.query(UserSecurityToken).filter(
        UserSecurityToken.token_hash == hash_security_token(raw_token),
        UserSecurityToken.token_type == token_type,
        UserSecurityToken.used_at.is_(None),
        UserSecurityToken.expires_at > datetime.utcnow(),
    ).first()
    if not token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired security token")
    token.used_at = datetime.utcnow()
    return token.user


def _security_email_url(path: str, token: str) -> str:
    # The frontend should replace this base URL in deployment-specific email templates.
    return f"{settings.CORS_ORIGINS[0] if isinstance(settings.CORS_ORIGINS, list) else 'http://localhost:3000'}{path}?token={quote(token)}"


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def register(
    request: Request,
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """Register a public user.

    Privileged operational roles must be assigned by an administrator after review.
    """
    existing_user = db.query(User).filter(
        (User.email == user_data.email) | (User.username == user_data.username)
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email or username already registered"
        )

    role = db.query(Role).filter(Role.name == SELF_REGISTRATION_ROLE).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Public role is not configured"
        )

    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        email=user_data.email,
        username=user_data.username,
        full_name=user_data.full_name,
        hashed_password=hashed_password,
        role_id=role.id,
        country_id=user_data.country_id,
        is_active=True,
        is_verified=False,
    )

    db.add(new_user)
    db.flush()

    audit_log = AuditLog(
        user_id=new_user.id,
        action=AuditAction.CREATE,
        resource_type="user",
        resource_id=new_user.id,
        details={
            "action": "user_registration",
            "requested_role_id": user_data.role_id,
            "assigned_role": SELF_REGISTRATION_ROLE,
        }
    )
    db.add(audit_log)
    verification_token = _issue_security_token(db, new_user, EMAIL_VERIFICATION_TOKEN)
    db.commit()
    db.refresh(new_user)

    if settings.SMTP_USER and settings.SMTP_PASSWORD:
        try:
            AuthEmailService.send(
                new_user.email,
                "Verify your EpiSphere email address",
                f"Verify your account using this link: {_security_email_url('/auth/verify-email', verification_token)}",
            )
        except Exception:
            # Do not expose SMTP details or token contents to the client.
            pass

    return new_user


@router.post("/login", response_model=Token)
@limiter.limit("5/minute")
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Login and get access token"""
    login_identifier = form_data.username.strip()
    user = db.query(User).filter(
        (User.username == login_identifier) | (User.email == login_identifier)
    ).first()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account"
        )

    if settings.EMAIL_VERIFICATION_REQUIRED and not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email verification is required before sign in",
        )

    role_name = (user.role.name if user.role else "").lower()
    if settings.MFA_REQUIRED_FOR_PRIVILEGED and role_name in PRIVILEGED_ROLES and not user.mfa_enabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Privileged users must enroll MFA before sign in",
        )
    if user.mfa_enabled and role_name in PRIVILEGED_ROLES:
        challenge_token = create_mfa_challenge_token(
            {"sub": str(user.id), "ver": user.token_version or 0},
            expires_delta=timedelta(minutes=settings.MFA_CHALLENGE_EXPIRE_MINUTES),
        )
        return {
            "access_token": None,
            "token_type": "bearer",
            "mfa_required": True,
            "mfa_challenge_token": challenge_token,
        }

    user.last_login = datetime.utcnow()
    db.flush()

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id), "username": user.username, "ver": user.token_version or 0},
        expires_delta=access_token_expires
    )

    audit_log = AuditLog(
        user_id=user.id,
        action=AuditAction.LOGIN,
        resource_type="auth",
        details={"action": "user_login"}
    )
    db.add(audit_log)
    db.commit()

    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """Get current user information"""
    return current_user


@router.post("/verify-email", response_model=UserResponse)
@limiter.limit("10/minute")
async def verify_email(
    request: Request,
    payload: VerifyEmailRequest,
    db: Session = Depends(get_db),
):
    user = _consume_security_token(db, payload.token, EMAIL_VERIFICATION_TOKEN)
    user.is_verified = True
    db.add(AuditLog(
        user_id=user.id,
        action=AuditAction.UPDATE,
        resource_type="auth",
        resource_id=user.id,
        details={"action": "email_verified"},
    ))
    db.commit()
    db.refresh(user)
    return user


@router.post("/request-password-reset")
@limiter.limit("5/hour")
async def request_password_reset(
    request: Request,
    payload: PasswordResetRequest,
    db: Session = Depends(get_db),
):
    """Request a reset without revealing whether the email exists."""
    user = db.query(User).filter(User.email == payload.email).first()
    if user:
        reset_token = _issue_security_token(db, user, PASSWORD_RESET_TOKEN)
        db.commit()
        if settings.SMTP_USER and settings.SMTP_PASSWORD:
            try:
                AuthEmailService.send(
                    user.email,
                    "Reset your EpiSphere password",
                    f"Reset your password using this link: {_security_email_url('/auth/reset-password', reset_token)}",
                )
            except Exception:
                pass
    return {"message": "If the account exists, password-reset instructions have been sent."}


@router.post("/reset-password")
@limiter.limit("10/minute")
async def reset_password(
    request: Request,
    payload: PasswordResetConfirm,
    db: Session = Depends(get_db),
):
    user = _consume_security_token(db, payload.token, PASSWORD_RESET_TOKEN)
    user.hashed_password = get_password_hash(payload.password)
    user.token_version = (user.token_version or 0) + 1
    db.add(AuditLog(
        user_id=user.id,
        action=AuditAction.UPDATE,
        resource_type="auth",
        resource_id=user.id,
        details={"action": "password_reset", "sessions_revoked": True},
    ))
    db.commit()
    return {"message": "Password reset successfully. Please sign in again."}


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Revoke all JWT sessions issued before this logout."""
    current_user.token_version = (current_user.token_version or 0) + 1
    db.add(AuditLog(
        user_id=current_user.id,
        action=AuditAction.LOGOUT,
        resource_type="auth",
        resource_id=current_user.id,
        details={"action": "logout", "sessions_revoked": True},
    ))
    db.commit()
    return {"message": "Signed out"}


@router.post("/mfa/setup", response_model=MfaSetupResponse)
async def setup_mfa(
    current_user: User = Depends(require_role(list(PRIVILEGED_ROLES))),
    db: Session = Depends(get_db),
):
    secret = generate_totp_secret()
    current_user.mfa_pending_secret = secret
    db.commit()
    label = quote(f"EpiSphere:{current_user.email}")
    uri = f"otpauth://totp/{label}?secret={secret}&issuer=EpiSphere&algorithm=SHA1&digits=6&period=30"
    return {"secret": secret, "otpauth_uri": uri}


@router.post("/mfa/enable")
async def enable_mfa(
    payload: MfaCodeRequest,
    current_user: User = Depends(require_role(list(PRIVILEGED_ROLES))),
    db: Session = Depends(get_db),
):
    if not current_user.mfa_pending_secret or not verify_totp_code(current_user.mfa_pending_secret, payload.code):
        raise HTTPException(status_code=400, detail="Invalid MFA code or setup session")
    current_user.mfa_secret = current_user.mfa_pending_secret
    current_user.mfa_pending_secret = None
    current_user.mfa_enabled = True
    db.add(AuditLog(
        user_id=current_user.id,
        action=AuditAction.UPDATE,
        resource_type="auth",
        resource_id=current_user.id,
        details={"action": "mfa_enabled"},
    ))
    db.commit()
    return {"message": "MFA enabled"}


@router.post("/mfa/disable")
async def disable_mfa(
    payload: MfaCodeRequest,
    current_user: User = Depends(require_role(list(PRIVILEGED_ROLES))),
    db: Session = Depends(get_db),
):
    if not current_user.mfa_secret or not verify_totp_code(current_user.mfa_secret, payload.code):
        raise HTTPException(status_code=400, detail="Invalid MFA code")
    current_user.mfa_enabled = False
    current_user.mfa_secret = None
    current_user.mfa_pending_secret = None
    current_user.token_version = (current_user.token_version or 0) + 1
    db.commit()
    return {"message": "MFA disabled and sessions revoked"}


@router.post("/mfa/verify", response_model=Token)
@limiter.limit("10/minute")
async def verify_mfa(
    request: Request,
    payload: MfaVerifyRequest,
    db: Session = Depends(get_db),
):
    challenge = decode_access_token(payload.challenge_token)
    if not challenge or challenge.get("token_type") != "mfa_challenge":
        raise HTTPException(status_code=401, detail="Invalid or expired MFA challenge")
    try:
        user_id = int(challenge.get("sub"))
    except (TypeError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid MFA challenge")
    user = db.query(User).filter(User.id == user_id, User.is_active.is_(True)).first()
    if not user or challenge.get("ver") != (user.token_version or 0) or not user.mfa_enabled or not user.mfa_secret:
        raise HTTPException(status_code=401, detail="Invalid or expired MFA challenge")
    if not verify_totp_code(user.mfa_secret, payload.code):
        raise HTTPException(status_code=401, detail="Invalid MFA code")

    user.last_login = datetime.utcnow()
    db.add(AuditLog(
        user_id=user.id,
        action=AuditAction.LOGIN,
        resource_type="auth",
        resource_id=user.id,
        details={"action": "mfa_login"},
    ))
    db.commit()
    return {
        "access_token": create_access_token(
            {"sub": str(user.id), "username": user.username, "ver": user.token_version or 0}
        ),
        "token_type": "bearer",
    }
