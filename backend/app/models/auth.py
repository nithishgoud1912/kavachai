"""Request and response models for local, air-gapped authentication."""

from pydantic import BaseModel, Field
from typing import Literal


class BootstrapRequest(BaseModel):
    bootstrap_token: str = Field(min_length=16)
    username: str = Field(min_length=3, max_length=128, pattern=r"^[A-Za-z0-9._-]+$")
    password: str = Field(min_length=14, max_length=256)
    department: str = Field(min_length=1, max_length=128)


class LoginRequest(BaseModel):
    username: str = Field(min_length=3, max_length=128)
    password: str = Field(min_length=1, max_length=256)


class MfaVerifyRequest(BaseModel):
    session_id: str
    code: str = Field(pattern=r"^\d{6}$")


class CreateUserRequest(BaseModel):
    username: str = Field(min_length=3, max_length=128, pattern=r"^[A-Za-z0-9._-]+$")
    password: str = Field(min_length=14, max_length=256)
    department: str = Field(min_length=1, max_length=128)
    clearance: Literal["public_demo", "internal", "confidential", "restricted", "defence_sensitive"] = "internal"
    roles: list[str] = Field(default_factory=lambda: ["ai_workbench_user"])


class AssignRolesRequest(BaseModel):
    roles: list[str] = Field(min_length=1)


class AuthResponse(BaseModel):
    session_id: str | None = None
    mfa_required: bool = False
    expires_at: str | None = None
    user_id: str | None = None
    username: str | None = None
    department: str | None = None
    roles: list[str] = Field(default_factory=list)


class UserResponse(BaseModel):
    id: str
    username: str
    department: str
    clearance: str
    roles: list[str]
    is_active: bool
    mfa_enabled: bool
