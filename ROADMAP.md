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
- `Instance` model: id, name, type (saas | private | enterprise), base_url, enabled_services, health_status
- CRUD API: `POST /api/v1/instances`, `GET`, `PATCH`, `DELETE`
- Per-instance service record: cms_url, pm_url, pim_url, erp_url, ai_url

### Health monitoring
- Background job polls `/health/live` on every registered service every 30 s
- Aggregated status stored (last checked, latency, up/down streak)
- `GET /api/v1/instances/{id}/health` returns per-service health snapshot

### Instances dashboard (frontend)
- Card grid: instance name, type badge, service health tiles, last-seen timestamp
- Click → Instance detail page (tabs: Overview | Logs | Config | Members)

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
