# Xephon Admin — Roadmap

## Vision

Xephon Admin is the **central control hub** for all Xephon deployments.
A single place to manage users, monitor service health, control infrastructure,
and onboard tenants — whether the deployment is a hosted SaaS instance
(like Asana or Wrike) or a private cloud installation on Hetzner or
corporate infrastructure.

## Deployment models

| Model | Description |
|---|---|
| **Hosted SaaS** | Xephon-operated, multi-tenant, shared infrastructure. Tenants sign up, pay, and get isolated workspaces. |
| **Private cloud** | Customer-operated on Hetzner, AWS, or company-internal hardware. Single-tenant. Admin is the operator's control plane. |
| **Enterprise self-hosted** | Like private cloud but with Kubernetes, SSO federation, and corporate policy enforcement. |

---

## Phase 1 — Foundation (current)

**Status:** ✅ Shipped

- User management (invite, disable, enable, reset password)
- Role assignment (global roles across services)
- Audit log
- JWT / Keycloak-backed authentication
- CI/CD pipelines passing for both Python 3.12 and 3.13

---

## Phase 2 — Centralized Hub Architecture

**Goal:** Make xephon-admin the authoritative registry and control plane for
all deployed Xephon service instances.

### Instance & service registry
- [x] **Done (2026-07-27):** `Instance` model (`app/models/instance.py`) — id
      (server-generated UUID), name, type (plain string, Pydantic-validated
      at the API boundary as `Literal["saas", "private", "enterprise"]` —
      no DB-level enum, matching this codebase's existing style, e.g.
      `Service` has no enum columns either), base_url, enabled_services
      (JSONB list of strings), health_status (plain string, defaults
      `"unknown"`). Per-instance service record fields (cms_url/pm_url/
      pim_url/erp_url/ai_url, all nullable) live as columns on the same
      row rather than a child table — a "record", not a one-to-many
      relationship, per the roadmap's own wording. CRUD API mirrors
      `services.py`'s exact shape (`POST/GET/GET one/PATCH/DELETE
      /api/v1/instances`), audit-logged the same way (`instance.create`/
      `.update`/`.delete`). 11 new tests (`tests/test_instances.py`), 46
      total passing, clean ruff check/format. Confirmed live against the
      real running dev server (401 without a token, same auth gate as
      every other route). **Found and fixed a pre-existing gap along the
      way:** `alembic/script.py.mako` didn't exist in this repo at all —
      `alembic revision --autogenerate` couldn't generate *any* new
      migration until it was added (matched to this repo's existing
      migration's actual style, not alembic's raw default template).
      **Not done:** health monitoring (the background poller, aggregated
      status, and `/health/{id}/health` snapshot endpoint below) and the
      frontend Instances dashboard — see their own sections, both
      separately scoped and unstarted.

### Health monitoring
- [x] **Done (2026-07-29):** Background poller (`app/services/health_poller.py`)
      started as an `asyncio.create_task` from a FastAPI `lifespan` context
      manager in `main.py` (no new scheduler dependency), running `poll_once`
      every 30 s (`POLL_INTERVAL_SECONDS`) until cancelled on shutdown.
      `poll_once` walks every registered `Instance` and, for each configured
      service URL (cms/pm/pim/erp/ai — a service with no URL set is skipped
      entirely, not reported as down), does a `GET {base_url}/health/live`
      with a 5 s timeout: 200 → `"up"`, anything else (non-200, timeout,
      connection error) → `"down"`. Per-service snapshot (`status`,
      `checked_at`, `latency_ms`, `streak`) is stored in a new
      `Instance.health` JSONB column (`streak` increments on repeated status,
      resets to 1 on a change); the existing `health_status` column is
      derived from it (`"unknown"` if nothing configured, `"up"`/`"down"` if
      uniform, `"degraded"` if mixed) and kept as the at-a-glance summary
      field the Instances list already showed. New `GET
      /api/v1/instances/{id}/health` route returns the full per-service
      breakdown (`InstanceHealthRead`); `InstanceRead` itself also gained a
      `health` field so the list/detail routes already carry it without a
      second round-trip. 15 new tests (`test_health_poller.py` covering
      up/down/timeout/connection-error/streak/degraded-mixed/skip-
      unconfigured cases via `httpx.MockTransport` — no new test dependency
      — plus 3 in `test_instances.py` for the new route), 61 total passing,
      clean ruff/mypy-free (this repo has no mypy configured at all — only
      xephon-cms/erp/pim do), migration round-trip verified.
      **Cross-repo prerequisite fixed along the way:** the poller's honest
      behavior (no `/health/live` response looks identical to "actually
      down") meant xephon-cms and xephon-ai genuinely had no way to report
      "up" — xephon-cms only exposed a plain `/health` (different shape,
      no liveness/readiness split) and xephon-ai had no health endpoint at
      all. Added `/health/live` (always 200) and `/health/ready` (DB
      reachability via `SELECT 1`, 503 until up) to both, mirroring the
      exact convention already established in xephon-pm/xephon-pim/xephon-erp
      — xephon-cms kept its old `/health` alongside for backward
      compatibility. Frontend (`InstancesPage.tsx`) gained a click-to-expand
      per-service breakdown under each instance's health badge (status,
      streak, latency, last-checked time) — see "Instances dashboard"
      below. **Found and fixed a pre-existing, unrelated bug along the
      way:** the `degraded` health badge referenced a `badge-yellow` CSS
      class that was never defined (only `badge-green`/`badge-gray`/
      `badge-red`/`badge-purple` existed), so a degraded instance silently
      rendered unstyled — added the missing class. **Verified end-to-end
      against a real running stack:** started xephon-admin's backend
      (against a real Postgres) and frontend, registered a real Keycloak
      test user with the `xephon:admin` role, logged in through an actual
      browser (Playwright), created an Instance with its `cms_url` pointed
      at the real, already-running xephon-cms dev server and its `erp_url`
      pointed at an unreachable port, waited a full 30 s poll cycle, and
      confirmed in the UI: CMS genuinely resolved to "up" (6 ms latency),
      ERP genuinely resolved to "down", and the instance's overall badge
      showed "degraded" — proving the poller, the persisted snapshot, the
      route, and the frontend all agree end-to-end, not just against
      mocked unit tests.

### Instances dashboard (frontend)
- [x] **Done (2026-07-28):** `InstancesPage.tsx` — list/create/edit/delete
      for the Instance model above, mirroring `ServicesPage.tsx`'s exact
      CRUD pattern (same card-per-row layout, inline edit forms, badge
      styling) rather than a true multi-column "card grid." Shows type
      and `health_status` badges and the five per-instance service URLs.
      Wired into the nav bar and router. Verified: `tsc -b && vite build`
      (matching CI's own build step) succeeds, lint clean, and a static
      render of the page against the real compiled stylesheet looks
      correct — full interactive click-through wasn't possible (no
      stored Keycloak credentials in this environment, same limitation
      noted throughout this family of repos' work).
      **Not done, deliberately scoped out:** the click-through Instance
      detail page with Overview/Logs/Config/Members tabs — "Logs" needs
      Phase 3's container log streaming (unbuilt) and "Members" isn't a
      concept that exists on `Instance` at all yet; building a detail
      page around two not-yet-real features would mean inventing scope
      rather than implementing what's actually decided. Health status was
      shown as whatever's stored, not live-polled, when this bullet was
      first written — since fixed, see "Health monitoring" above (now
      done): the badge reflects the real poller and expands to a
      per-service breakdown.

---

## Phase 3 — Ops Dashboard (private-cloud / dev)

**Goal:** Start, stop, and observe Docker containers directly from the Admin UI.
Relevant for private-cloud deployments where xephon-admin has Docker socket
access. SaaS tenants do not use this feature.

### Backend
- Docker Engine API wrapper (docker-py): start / stop / restart containers
- WebSocket endpoint streaming container logs in real time
- Stats polling: CPU%, memory MB every 5 s via Docker stats API

### Frontend
- Container control buttons (Start / Stop / Restart) with confirmation dialog
- Live log panel (WebSocket) with filter and scroll-lock
- Sparklines for CPU and memory per service container

---

## Phase 4 — Multi-Tenant SaaS

**Goal:** Full tenant lifecycle for the hosted SaaS model.

### Tenant onboarding
- Signup flow: company name + admin email → provision Keycloak realm/client,
  create DB schemas, send invitation email with login link
- Automated provisioning idempotent (safe to retry)

### Identity federation
- Keycloak topology decision: realm-per-tenant vs shared realm with per-tenant clients
- Cross-service user provisioning: adding a user in Admin propagates to CMS, PM, PIM, ERP
- Deprovisioning: removing a user revokes access across all services

### Usage metering & quotas
- Middleware counting API calls per tenant per service, stored as daily aggregates
- Quota enforcement (configurable per plan)
- Usage API for billing integration

---

## Phase 5 — Infrastructure as Code

**Goal:** One-command deployment to any supported target.

### Private cloud (Hetzner)
- `docker-compose.yml` stack: all Xephon services with correct networking, volumes,
  env templates, and health checks
- Terraform module: Hetzner server + floating IP + firewall + DNS

### Enterprise (Kubernetes)
- Helm chart for all Xephon services
- Configurable: storage class, ingress class, resource limits, external Postgres/Redis
- Compatible with ArgoCD / Flux GitOps workflows

---

## Decisions log

| Date | Decision | Rationale |
|---|---|---|
| 2026-07-19 | Ops dashboard goes in xephon-infra services/ops, surfaced through xephon-admin UI | Keeps infrastructure concerns out of the application-level admin codebase; Admin calls the ops service API |
| 2026-07-19 | Keycloak topology: decide realm-per-tenant vs shared in Phase 4 | Requires load/isolation benchmarks before committing |
