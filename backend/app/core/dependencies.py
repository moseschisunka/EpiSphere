"""
FastAPI dependencies for authorization and permissions
"""

from typing import List
from fastapi import Depends, HTTPException, status

from app.core.security import get_current_user
from app.db.models import User


def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Dependency to ensure user is active"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
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


def require_role(allowed_roles: List[str]):
    """Dependency factory for role-based access control."""

    def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        user_role = current_user.role.name if current_user.role else None

        if user_role not in allowed_roles:
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

    def __call__(self, user: User = Depends(get_current_active_user)) -> User:
        if not user.role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no role assigned",
            )
        if user.role.name not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{user.role.name}' does not have permission to perform this action",
            )
        return user


allow_admin = RoleChecker(["admin"])
allow_clinician = RoleChecker(["clinician", "facility_admin", "admin"])
allow_pharmacist = RoleChecker(["pharmacist", "facility_admin", "admin"])
allow_facility_admin = RoleChecker(["facility_admin", "admin"])
