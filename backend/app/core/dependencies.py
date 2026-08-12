"""
FastAPI dependencies for authorization and permissions (RBAC)
"""

from typing import List, Optional
import hmac
import os
from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.core.database import get_db
from app.db.models import User, AuditLog, AuditAction


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

def get_agent_or_admin(
    request: Request,
    db: Session = Depends(get_db)
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
    configured_key = os.environ.get("AGENT_API_KEY")
    if api_key and configured_key and hmac.compare_digest(api_key, configured_key):
        return "agent"

    # 2. Check JWT Bearer
    auth_header = request.headers.get("authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1].strip()
        payload = decode_access_token(token)
        if payload:
            user_id = payload.get("sub")
            if user_id:
                user = db.query(User).filter(User.id == int(user_id)).first()
                if user and user.is_active and user.role and getattr(user.role, 'name', '').lower() == "admin":
                    return user

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Valid X-API-Key or Admin Bearer token required",
    )
