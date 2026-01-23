"""
FastAPI dependencies for authorization and permissions
"""

from typing import List
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.db.models import User, Role


def require_role(allowed_roles: List[str]):
    """
    Dependency factory for role-based access control
    Usage: @app.get("/admin", dependencies=[Depends(require_role(["admin"]))])
    """
    def role_checker(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ):
        user_role = current_user.role.name if current_user.role else None
        
        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {', '.join(allowed_roles)}"
            )
        return current_user
    
    return role_checker


def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Dependency to ensure user is active"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return current_user
