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

    `health` is the per-service snapshot a background job
    (app/services/health_poller.py) keeps current by polling each
    configured service URL's `/health/live` every 30s -- keyed by service
    name ("cms"/"pm"/"pim"/"erp"/"ai"), each entry
    {status, checked_at, latency_ms, streak}. `health_status` is the
    derived overall status ("up" all configured services responding,
    "down" all unreachable, "degraded" a mix, "unknown" nothing
    configured/polled yet) -- also settable directly via PATCH for manual
    overrides, same as before this existed.
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
    health: Mapped[dict] = mapped_column(JSONB, default=dict)

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
