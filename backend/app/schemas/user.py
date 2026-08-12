"""User schemas"""

from pydantic import BaseModel, EmailStr, ConfigDict, Field
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
    mfa_enabled: bool = False
    roles: list[str] = []
    created_at: datetime
    last_login: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: Optional[str] = None
    token_type: str = "bearer"
    mfa_required: bool = False
    mfa_challenge_token: Optional[str] = None


class TokenData(BaseModel):
    user_id: Optional[int] = None


class VerifyEmailRequest(BaseModel):
    token: str


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    password: str = Field(..., min_length=8)


class MfaCodeRequest(BaseModel):
    code: str


class MfaVerifyRequest(BaseModel):
    challenge_token: str
    code: str


class MfaSetupResponse(BaseModel):
    secret: str
    otpauth_uri: str

