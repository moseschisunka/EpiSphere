"""User schemas"""

from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    email: EmailStr
    username: str
    full_name: Optional[str] = None


class UserCreate(UserBase):
    password: str
    role_id: int
    country_id: Optional[int] = None


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    country_id: Optional[int] = None


class UserAdminUpdate(UserUpdate):
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    facility_id: Optional[int] = None


class UserRoleUpdate(BaseModel):
    role_id: int
    facility_id: Optional[int] = None
    country_id: Optional[int] = None
    is_verified: bool = True


class UserResponse(UserBase):
    id: int
    role_id: int
    country_id: Optional[int] = None
    facility_id: Optional[int] = None
    is_active: bool
    is_verified: bool
    created_at: datetime
    last_login: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: Optional[int] = None

