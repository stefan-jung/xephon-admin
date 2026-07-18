from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import String, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    actor_subject: Mapped[str] = mapped_column(String(128))
    actor_email: Mapped[str] = mapped_column(String(255), default="")
    action: Mapped[str] = mapped_column(String(128))
    target_user_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    target_user_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    details: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=text("now()"))
