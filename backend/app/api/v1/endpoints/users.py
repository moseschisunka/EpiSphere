"""User management endpoints"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_active_user, require_role
from app.db.models import AuditAction, AuditLog, Role, User
from app.schemas.user import UserAdminUpdate, UserResponse, UserRoleUpdate, UserUpdate

router = APIRouter()


@router.get("/roles")
async def list_roles(
    current_user: User = Depends(require_role(["admin"])),
    db: Session = Depends(get_db),
):
    """List assignable roles for the administrator access workspace."""
    return [
        {"id": role.id, "name": role.name, "description": role.description}
        for role in db.query(Role).order_by(Role.name).all()
    ]


@router.get("/", response_model=List[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_role(["admin"])),
    db: Session = Depends(get_db)
):
    """List all users (admin only)"""
    return db.query(User).offset(skip).limit(limit).all()


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get user by ID"""
    if current_user.id != user_id and current_user.role.name != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this user"
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return user


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update user profile fields. Admin-only fields use dedicated admin endpoints."""
    if current_user.id != user_id and current_user.role.name != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this user"
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    for field, value in user_update.model_dump(exclude_unset=True).items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)
    return user


@router.put("/{user_id}/admin", response_model=UserResponse)
async def admin_update_user(
    user_id: int,
    user_update: UserAdminUpdate,
    current_user: User = Depends(require_role(["admin"])),
    db: Session = Depends(get_db),
):
    """Update administrative user fields."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    for field, value in user_update.model_dump(exclude_unset=True).items():
        setattr(user, field, value)

    db.add(AuditLog(
        user_id=current_user.id,
        action=AuditAction.UPDATE,
        resource_type="user",
        resource_id=user.id,
        details={"action": "admin_user_update", "fields": list(user_update.model_dump(exclude_unset=True).keys())},
    ))
    db.commit()
    db.refresh(user)
    return user


@router.put("/{user_id}/role", response_model=UserResponse)
async def assign_user_role(
    user_id: int,
    role_update: UserRoleUpdate,
    current_user: User = Depends(require_role(["admin"])),
    db: Session = Depends(get_db),
):
    """Assign an operational role after administrative review."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    role = db.query(Role).filter(Role.id == role_update.role_id).first()
    if not role:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid role")

    previous_role_id = user.role_id
    user.role_id = role.id
    user.facility_id = role_update.facility_id
    user.country_id = role_update.country_id
    user.is_verified = role_update.is_verified

    db.add(AuditLog(
        user_id=current_user.id,
        action=AuditAction.UPDATE,
        resource_type="user",
        resource_id=user.id,
        details={
            "action": "role_assignment",
            "previous_role_id": previous_role_id,
            "new_role_id": role.id,
            "facility_id": role_update.facility_id,
            "country_id": role_update.country_id,
        },
    ))
    db.commit()
    db.refresh(user)
    return user
