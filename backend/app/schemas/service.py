from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class ServiceCreate(BaseModel):
    slug: str
    name: str
    base_url: str = ""
    enabled: bool = True
    roles: list[str] = []


class ServiceUpdate(BaseModel):
    name: str | None = None
    base_url: str | None = None
    enabled: bool | None = None
    roles: list[str] | None = None


class ServiceRead(BaseModel):
    slug: str
    name: str
    base_url: str
    enabled: bool
    roles: list[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
