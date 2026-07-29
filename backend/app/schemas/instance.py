from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel

InstanceType = Literal["saas", "private", "enterprise"]


class ServiceHealthEntry(BaseModel):
    status: Literal["up", "down"]
    checked_at: datetime
    latency_ms: float | None
    streak: int


class InstanceCreate(BaseModel):
    name: str
    type: InstanceType
    base_url: str = ""
    enabled_services: list[str] = []
    health_status: str = "unknown"
    cms_url: str | None = None
    pm_url: str | None = None
    pim_url: str | None = None
    erp_url: str | None = None
    ai_url: str | None = None


class InstanceUpdate(BaseModel):
    name: str | None = None
    type: InstanceType | None = None
    base_url: str | None = None
    enabled_services: list[str] | None = None
    health_status: str | None = None
    cms_url: str | None = None
    pm_url: str | None = None
    pim_url: str | None = None
    erp_url: str | None = None
    ai_url: str | None = None


class InstanceRead(BaseModel):
    id: uuid.UUID
    name: str
    type: str
    base_url: str
    enabled_services: list[str]
    health_status: str
    health: dict[str, ServiceHealthEntry]
    cms_url: str | None
    pm_url: str | None
    pim_url: str | None
    erp_url: str | None
    ai_url: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class InstanceHealthRead(BaseModel):
    instance_id: uuid.UUID
    health_status: str
    services: dict[str, ServiceHealthEntry]
