"""
FastAPI dependencies for authorization and permissions (RBAC)
"""

from dataclasses import dataclass
from typing import List
import hmac
from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import get_current_user
from app.core.database import get_db
from app.db.models import User, AuditLog, AuditAction


SCOPED_OPERATIONAL_ROLES = {
    "country_data_officer",
    "facility_admin",
    "clinician",
    "pharmacist",
}


def user_role_name(user: User) -> str:
    return (getattr(getattr(user, "role", None), "name", "") or "").lower()


def is_admin_user(user: User) -> bool:
    return user_role_name(user) == "admin" or bool(getattr(user, "is_superuser", False))


def get_user_country_scope(user: User) -> int | None:
    """Return the user's effective country scope, including facility inheritance."""
    if user.country_id:
        return user.country_id
    facility = getattr(user, "facility", None)
    return getattr(facility, "country_id", None) if facility else None


def enforce_country_scope(user: User, country_id: int) -> None:
    """Fail closed when a scoped operator targets another country or has no scope."""
    if is_admin_user(user):
        return

    scope = get_user_country_scope(user)
    role = user_role_name(user)
    if role in SCOPED_OPERATIONAL_ROLES and scope is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operational user is not assigned to a country or facility",
        )
    if scope is not None and scope != country_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Requested country is outside the user's authorized scope",
        )


def apply_country_scope(query, model, user: User):
    """Constrain a SQLAlchemy query to the user's country where applicable."""
    if is_admin_user(user):
        return query

    scope = get_user_country_scope(user)
    if user_role_name(user) in SCOPED_OPERATIONAL_ROLES and scope is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operational user is not assigned to a country or facility",
        )
    return query.filter(getattr(model, "country_id") == scope) if scope is not None else query


def enforce_facility_scope(user: User, facility_id: int) -> None:
    """Fail closed for facility administrators outside their assigned facility."""
    if is_admin_user(user):
        return
    if user_role_name(user) == "facility_admin":
        if not user.facility_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Facility administrator is not assigned to a facility",
            )
        if user.facility_id != facility_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Requested facility is outside the user's authorized scope",
            )


def apply_facility_scope(query, model, user: User):
    if is_admin_user(user):
        return query
    enforce_facility_scope(user, user.facility_id or 0)
    return query.filter(getattr(model, "id") == user.facility_id)


def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Dependency to ensure user is active"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account",
        )
    return current_user


def get_current_facility_user(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """Dependency to ensure user is assigned to a facility."""
    if not current_user.facility_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not assigned to a facility",
        )
    return current_user


def has_role_access(user: User, allowed_roles: List[str]) -> bool:
    """
    Check if a user possesses one of the allowed roles or admin privileges.
    Admins automatically inherit access to all role-restricted resources.
    """
    if not user.is_active:
        return False

    user_role = user.role.name.lower() if user.role else ""
    
    # Admin role or superuser status grants universal access across all endpoints
    if user_role == "admin" or getattr(user, "is_superuser", False):
        return True

    allowed_lower = [r.lower() for r in allowed_roles]
    return user_role in allowed_lower


def require_role(allowed_roles: List[str]):
    """Dependency factory for role-based access control with audit logging."""

    def role_checker(
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ) -> User:
        if not has_role_access(current_user, allowed_roles):
            # Log access denial for security audit
            try:
                audit = AuditLog(
                    user_id=current_user.id,
                    action=AuditAction.VIEW,
                    resource_type="rbac_denial",
                    details={
                        "attempted_roles": allowed_roles,
                        "actual_role": current_user.role.name if current_user.role else "none",
                    }
                )
                db.add(audit)
                db.commit()
            except Exception:
                db.rollback()

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {', '.join(allowed_roles)}",
            )
        return current_user

    return role_checker


class RoleChecker:
    """Reusable role checker for endpoint dependencies."""

    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles

    def __call__(
        self,
        user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ) -> User:
        if not user.role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no role assigned",
            )

        if not has_role_access(user, self.allowed_roles):
            # Log security access refusal
            try:
                audit = AuditLog(
                    user_id=user.id,
                    action=AuditAction.VIEW,
                    resource_type="rbac_denial",
                    details={
                        "allowed_roles": self.allowed_roles,
                        "user_role": user.role.name,
                    }
                )
                db.add(audit)
                db.commit()
            except Exception:
                db.rollback()

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{user.role.name}' does not have permission to perform this action",
            )
        return user


# Pre-defined RBAC Guards
allow_admin = RoleChecker(["admin"])
allow_epidemiologist = RoleChecker(["admin", "epidemiologist"])
allow_facility_admin = RoleChecker(["admin", "facility_admin"])
allow_clinician = RoleChecker(["admin", "clinician", "facility_admin"])
allow_pharmacist = RoleChecker(["admin", "pharmacist", "facility_admin"])
allow_data_officer = RoleChecker(["admin", "epidemiologist", "country_data_officer", "facility_admin"])


@dataclass(frozen=True)
class ServicePrincipal:
    """Identity for a non-human integration caller."""

    name: str
    auth_method: str

def _get_agent_or_admin(
    request: Request,
    db: Session,
    scope: str | None = None,
):
    """
    Dependency that allows access if EITHER:
    1. A valid X-API-Key is provided (for n8n autonomous agents)
    2. A valid Bearer token for an Admin user is provided
    """
    from app.core.security import decode_access_token
    from app.db.models import User
    
    # 1. Check API Key
    api_key = request.headers.get("x-api-key")
    scoped_key = {
        "news": settings.NEWS_AGENT_API_KEY,
        "datasets": settings.DATASET_AGENT_API_KEY,
        "interop": settings.INTEROP_AGENT_API_KEY,
    }.get(scope)
    # Named n8n workflows must use their own revocable credential. The legacy
    # shared key remains available only to callers explicitly using the
    # unscoped dependency during a controlled migration.
    configured_key = scoped_key if scope is not None else settings.AGENT_API_KEY
    if api_key and configured_key and hmac.compare_digest(api_key, configured_key):
        return ServicePrincipal(
            name=f"n8n-{scope}" if scope else "n8n",
            auth_method="x-api-key",
        )

    # 2. Check JWT Bearer
    auth_header = request.headers.get("authorization")
    scheme, _, token = auth_header.partition(" ") if auth_header else ("", "", "")
    if scheme.lower() == "bearer" and token.strip():
        token = token.strip()
        payload = decode_access_token(token)
        if payload and payload.get("token_type") != "mfa_challenge":
            user_id = payload.get("sub")
            if user_id:
                try:
                    user_id = int(user_id)
                except (TypeError, ValueError):
                    user_id = None
                user = db.query(User).filter(User.id == user_id).first() if user_id else None
                if user and user.is_active and user.role and getattr(user.role, 'name', '').lower() == "admin":
                    return user

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Valid X-API-Key or Admin Bearer token required",
    )


def get_agent_or_admin(request: Request, db: Session = Depends(get_db)):
    return _get_agent_or_admin(request, db)


def get_news_agent_or_admin(request: Request, db: Session = Depends(get_db)):
    return _get_agent_or_admin(request, db, scope="news")


def get_dataset_agent_or_admin(request: Request, db: Session = Depends(get_db)):
    return _get_agent_or_admin(request, db, scope="datasets")


def get_interop_agent_or_admin(request: Request, db: Session = Depends(get_db)):
    return _get_agent_or_admin(request, db, scope="interop")
