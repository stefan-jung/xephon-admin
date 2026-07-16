from __future__ import annotations

from pydantic import BaseModel, EmailStr


class UserInvite(BaseModel):
    email: EmailStr
    username: str
    first_name: str = ""
    last_name: str = ""


class UserRead(BaseModel):
    id: str
    username: str
    email: str
    firstName: str = ""
    lastName: str = ""
    enabled: bool
    emailVerified: bool


class UserUpdate(BaseModel):
    firstName: str | None = None
    lastName: str | None = None
    email: str | None = None
    enabled: bool | None = None
