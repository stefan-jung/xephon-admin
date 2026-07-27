from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import String, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Instance(Base):
    """A deployed Xephon environment (a SaaS tenant, a private-cloud
    install, or an enterprise self-hosted one) — the Phase 2 "centralized
    hub" registry. Distinct from `Service`: `Service` catalogs the kinds
    of services that exist (cms/pm/pim/...) for role assignment purposes;
    `Instance` is one actual deployment, with its own URL per service.

    health_status is a plain, externally-set field here -- the background
    job that would actively poll each registered service's `/health/live`
    and keep it current is a separate, larger piece of Phase 2 (those
    endpoints don't exist on the other services yet) and isn't attempted
    in this pass.
    """

    __tablename__ = "instances"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    name: Mapped[str] = mapped_column(String(128))
    type: Mapped[str] = mapped_column(String(32))  # "saas" | "private" | "enterprise"
    base_url: Mapped[str] = mapped_column(String(255), default="")
    enabled_services: Mapped[list] = mapped_column(JSONB, default=list)
    health_status: Mapped[str] = mapped_column(String(32), default="unknown")

    # Per-instance service record: where this specific deployment's own
    # services live, distinct from `base_url` (the instance's own address).
    cms_url: Mapped[str | None] = mapped_column(String(255), default=None)
    pm_url: Mapped[str | None] = mapped_column(String(255), default=None)
    pim_url: Mapped[str | None] = mapped_column(String(255), default=None)
    erp_url: Mapped[str | None] = mapped_column(String(255), default=None)
    ai_url: Mapped[str | None] = mapped_column(String(255), default=None)

    created_at: Mapped[datetime] = mapped_column(server_default=text("now()"))
    updated_at: Mapped[datetime] = mapped_column(
        server_default=text("now()"),
        onupdate=datetime.now,
    )
