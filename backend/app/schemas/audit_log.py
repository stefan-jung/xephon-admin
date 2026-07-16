from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel


class AuditLogRead(BaseModel):
    id: uuid.UUID
    actor_subject: str
    actor_email: str
    action: str
    target_user_id: str | None
    target_user_email: str | None
    details: dict[str, Any] | None
    created_at: datetime

    model_config = {"from_attributes": True}
