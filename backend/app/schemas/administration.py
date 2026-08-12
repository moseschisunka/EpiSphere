"""Explicit administrator workspace response contracts."""

from pydantic import BaseModel, ConfigDict


class RoleResponse(BaseModel):
    id: int
    name: str
    description: str | None = None


class SourceSystemResponse(BaseModel):
    id: int
    name: str
    code: str
    system_type: str
    owner: str | None = None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)
