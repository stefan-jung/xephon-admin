import React, { useEffect, useState } from "react";
import { createInstance, deleteInstance, listInstances, updateInstance } from "../api/client";
import type { Instance } from "../api/types";

const SERVICE_URL_FIELDS = [
  { key: "cms_url", label: "CMS" },
  { key: "pm_url", label: "PM" },
  { key: "pim_url", label: "PIM" },
  { key: "erp_url", label: "ERP" },
  { key: "ai_url", label: "AI" },
] as const;

interface FormState {
  name: string;
  type: "saas" | "private" | "enterprise";
  base_url: string;
  enabled_services: string;
  cms_url: string;
  pm_url: string;
  pim_url: string;
  erp_url: string;
  ai_url: string;
}

const EMPTY_FORM: FormState = {
  name: "",
  type: "saas",
  base_url: "",
  enabled_services: "",
  cms_url: "",
  pm_url: "",
  pim_url: "",
  erp_url: "",
  ai_url: "",
};

function toInstance(form: FormState) {
  return {
    name: form.name,
    type: form.type,
    base_url: form.base_url,
    enabled_services: form.enabled_services
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean),
    cms_url: form.cms_url || undefined,
    pm_url: form.pm_url || undefined,
    pim_url: form.pim_url || undefined,
    erp_url: form.erp_url || undefined,
    ai_url: form.ai_url || undefined,
  };
}

function fromInstance(inst: Instance): FormState {
  return {
    name: inst.name,
    type: inst.type,
    base_url: inst.base_url,
    enabled_services: inst.enabled_services.join(", "),
    cms_url: inst.cms_url ?? "",
    pm_url: inst.pm_url ?? "",
    pim_url: inst.pim_url ?? "",
    erp_url: inst.erp_url ?? "",
    ai_url: inst.ai_url ?? "",
  };
}

const HEALTH_BADGE: Record<string, string> = {
  up: "badge-green",
  healthy: "badge-green",
  degraded: "badge-yellow",
  down: "badge-red",
  unknown: "badge-gray",
};

const SERVICE_LABELS: Record<string, string> = {
  cms: "CMS",
  pm: "PM",
  pim: "PIM",
  erp: "ERP",
  ai: "AI",
};

function formatCheckedAt(iso: string): string {
  return new Date(iso).toLocaleString();
}

function ServiceHealthBreakdown({ health }: { health: Instance["health"] }) {
  const entries = Object.entries(health);
  if (entries.length === 0) {
    return <p className="text-gray-500 text-xs mt-2">No health data yet — waiting on the next poll.</p>;
  }
  return (
    <div className="mt-2 space-y-1">
      {entries.map(([service, entry]) => (
        <div key={service} className="flex items-center gap-2 text-xs">
          <span className={`badge ${HEALTH_BADGE[entry.status] ?? "badge-gray"}`}>
            {SERVICE_LABELS[service] ?? service}: {entry.status}
          </span>
          <span className="text-gray-500">
            streak {entry.streak}
            {entry.latency_ms !== null ? ` · ${entry.latency_ms.toFixed(0)}ms` : ""} · checked{" "}
            {formatCheckedAt(entry.checked_at)}
          </span>
        </div>
      ))}
    </div>
  );
}

function ServiceUrlFields({
  form,
  onChange,
}: {
  form: FormState;
  onChange: (patch: Partial<FormState>) => void;
}) {
  return (
    <div className="grid grid-cols-2 gap-4">
      {SERVICE_URL_FIELDS.map(({ key, label }) => (
        <div key={key}>
          <label className="field-label">{label} URL</label>
          <input
            className="field-input"
            placeholder={`http://localhost:8000`}
            value={form[key]}
            onChange={(e) => onChange({ [key]: e.target.value })}
          />
        </div>
      ))}
    </div>
  );
}

export function InstancesPage() {
  const [instances, setInstances] = useState<Instance[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [msg, setMsg] = useState<string | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [editId, setEditId] = useState<string | null>(null);
  const [createForm, setCreateForm] = useState<FormState>(EMPTY_FORM);
  const [editForm, setEditForm] = useState<FormState>(EMPTY_FORM);
  const [expandedHealthId, setExpandedHealthId] = useState<string | null>(null);

  const load = () => {
    listInstances()
      .then(setInstances)
      .catch((err) => setError(String(err)));
  };

  useEffect(load, []);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    try {
      await createInstance(toInstance(createForm));
      setMsg(`Instance "${createForm.name}" created.`);
      setShowCreate(false);
      setCreateForm(EMPTY_FORM);
      load();
    } catch (err) {
      setError(String(err));
    }
  }

  function startEdit(inst: Instance) {
    setEditId(inst.id);
    setEditForm(fromInstance(inst));
  }

  async function handleEdit(e: React.FormEvent) {
    e.preventDefault();
    if (!editId) return;
    try {
      await updateInstance(editId, toInstance(editForm));
      setMsg(`Instance "${editForm.name}" updated.`);
      setEditId(null);
      load();
    } catch (err) {
      setError(String(err));
    }
  }

  async function handleDelete(inst: Instance) {
    try {
      await deleteInstance(inst.id);
      setMsg(`Instance "${inst.name}" deleted.`);
      load();
    } catch (err) {
      setError(String(err));
    }
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <h1 className="page-title">Instances</h1>
        <button className="btn btn-primary btn-sm" onClick={() => setShowCreate(!showCreate)}>
          + Add Instance
        </button>
      </div>

      {error && <div className="alert-error mb-4">{error}</div>}
      {msg && <div className="alert-success mb-4">{msg}</div>}

      {showCreate && (
        <form onSubmit={handleCreate} className="card mb-6 space-y-4">
          <h2 className="font-semibold">New instance</h2>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="field-label">Name *</label>
              <input
                className="field-input"
                required
                placeholder="Acme Private Cloud"
                value={createForm.name}
                onChange={(e) => setCreateForm((p) => ({ ...p, name: e.target.value }))}
              />
            </div>
            <div>
              <label className="field-label">Type *</label>
              <select
                className="field-input"
                value={createForm.type}
                onChange={(e) =>
                  setCreateForm((p) => ({ ...p, type: e.target.value as FormState["type"] }))
                }
              >
                <option value="saas">SaaS</option>
                <option value="private">Private cloud</option>
                <option value="enterprise">Enterprise self-hosted</option>
              </select>
            </div>
            <div>
              <label className="field-label">Base URL</label>
              <input
                className="field-input"
                placeholder="https://acme.xephon.example"
                value={createForm.base_url}
                onChange={(e) => setCreateForm((p) => ({ ...p, base_url: e.target.value }))}
              />
            </div>
            <div>
              <label className="field-label">Enabled services (comma-separated)</label>
              <input
                className="field-input"
                placeholder="cms, pm, pim"
                value={createForm.enabled_services}
                onChange={(e) =>
                  setCreateForm((p) => ({ ...p, enabled_services: e.target.value }))
                }
              />
            </div>
          </div>
          <ServiceUrlFields
            form={createForm}
            onChange={(patch) => setCreateForm((p) => ({ ...p, ...patch }))}
          />
          <div className="flex gap-2">
            <button type="submit" className="btn btn-primary btn-sm">
              Create
            </button>
            <button
              type="button"
              className="btn btn-ghost btn-sm"
              onClick={() => setShowCreate(false)}
            >
              Cancel
            </button>
          </div>
        </form>
      )}

      <div className="space-y-3">
        {instances.map((inst) => (
          <div key={inst.id} className="card">
            {editId === inst.id ? (
              <form onSubmit={handleEdit} className="space-y-3">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="field-label">Name</label>
                    <input
                      className="field-input"
                      value={editForm.name}
                      onChange={(e) => setEditForm((p) => ({ ...p, name: e.target.value }))}
                    />
                  </div>
                  <div>
                    <label className="field-label">Type</label>
                    <select
                      className="field-input"
                      value={editForm.type}
                      onChange={(e) =>
                        setEditForm((p) => ({ ...p, type: e.target.value as FormState["type"] }))
                      }
                    >
                      <option value="saas">SaaS</option>
                      <option value="private">Private cloud</option>
                      <option value="enterprise">Enterprise self-hosted</option>
                    </select>
                  </div>
                  <div>
                    <label className="field-label">Base URL</label>
                    <input
                      className="field-input"
                      value={editForm.base_url}
                      onChange={(e) => setEditForm((p) => ({ ...p, base_url: e.target.value }))}
                    />
                  </div>
                  <div>
                    <label className="field-label">Enabled services (comma-separated)</label>
                    <input
                      className="field-input"
                      value={editForm.enabled_services}
                      onChange={(e) =>
                        setEditForm((p) => ({ ...p, enabled_services: e.target.value }))
                      }
                    />
                  </div>
                </div>
                <ServiceUrlFields
                  form={editForm}
                  onChange={(patch) => setEditForm((p) => ({ ...p, ...patch }))}
                />
                <div className="flex gap-2">
                  <button type="submit" className="btn btn-primary btn-sm">
                    Save
                  </button>
                  <button
                    type="button"
                    className="btn btn-ghost btn-sm"
                    onClick={() => setEditId(null)}
                  >
                    Cancel
                  </button>
                </div>
              </form>
            ) : (
              <div className="flex items-start justify-between gap-4">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold">{inst.name}</span>
                    <span className="badge badge-gray">{inst.type}</span>
                    <button
                      type="button"
                      className={`badge ${HEALTH_BADGE[inst.health_status] ?? "badge-gray"}`}
                      onClick={() =>
                        setExpandedHealthId(expandedHealthId === inst.id ? null : inst.id)
                      }
                      title="Click to show per-service health"
                    >
                      {inst.health_status} {expandedHealthId === inst.id ? "▲" : "▼"}
                    </button>
                  </div>
                  {expandedHealthId === inst.id && (
                    <ServiceHealthBreakdown health={inst.health} />
                  )}
                  {inst.base_url && (
                    <p className="text-gray-500 text-xs font-mono">{inst.base_url}</p>
                  )}
                  {inst.enabled_services.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-1">
                      {inst.enabled_services.map((s) => (
                        <span key={s} className="badge badge-purple">
                          {s}
                        </span>
                      ))}
                    </div>
                  )}
                  {SERVICE_URL_FIELDS.some(({ key }) => inst[key]) && (
                    <div className="text-gray-500 text-xs font-mono mt-1 space-y-0.5">
                      {SERVICE_URL_FIELDS.filter(({ key }) => inst[key]).map(({ key, label }) => (
                        <div key={key}>
                          {label}: {inst[key]}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
                <div className="flex gap-2 shrink-0">
                  <button className="btn btn-ghost btn-sm" onClick={() => startEdit(inst)}>
                    Edit
                  </button>
                  <button className="btn btn-danger btn-sm" onClick={() => handleDelete(inst)}>
                    Delete
                  </button>
                </div>
              </div>
            )}
          </div>
        ))}
        {instances.length === 0 && (
          <div className="empty-state">No instances registered yet.</div>
        )}
      </div>
    </div>
  );
}
