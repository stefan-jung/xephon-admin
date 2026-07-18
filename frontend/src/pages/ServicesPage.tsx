import React, { useEffect, useState } from "react";
import { createService, listServices, updateService } from "../api/client";
import type { Service } from "../api/types";

export function ServicesPage() {
  const [services, setServices] = useState<Service[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [msg, setMsg] = useState<string | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [editSlug, setEditSlug] = useState<string | null>(null);
  const [createForm, setCreateForm] = useState({
    slug: "",
    name: "",
    base_url: "",
    roles: "",
  });
  const [editForm, setEditForm] = useState({
    name: "",
    base_url: "",
    roles: "",
  });

  const load = () => {
    listServices()
      .then(setServices)
      .catch((err) => setError(String(err)));
  };

  useEffect(load, []);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    try {
      await createService({
        slug: createForm.slug,
        name: createForm.name,
        base_url: createForm.base_url,
        roles: createForm.roles
          .split(",")
          .map((r) => r.trim())
          .filter(Boolean),
      });
      setMsg(`Service "${createForm.slug}" created.`);
      setShowCreate(false);
      setCreateForm({ slug: "", name: "", base_url: "", roles: "" });
      load();
    } catch (err) {
      setError(String(err));
    }
  }

  function startEdit(svc: Service) {
    setEditSlug(svc.slug);
    setEditForm({
      name: svc.name,
      base_url: svc.base_url,
      roles: svc.roles.join(", "),
    });
  }

  async function handleEdit(e: React.FormEvent) {
    e.preventDefault();
    if (!editSlug) return;
    try {
      await updateService(editSlug, {
        name: editForm.name,
        base_url: editForm.base_url,
        roles: editForm.roles
          .split(",")
          .map((r) => r.trim())
          .filter(Boolean),
      });
      setMsg(`Service "${editSlug}" updated.`);
      setEditSlug(null);
      load();
    } catch (err) {
      setError(String(err));
    }
  }

  async function toggleEnabled(svc: Service) {
    try {
      await updateService(svc.slug, { enabled: !svc.enabled });
      setMsg(`"${svc.name}" ${svc.enabled ? "disabled" : "enabled"}.`);
      load();
    } catch (err) {
      setError(String(err));
    }
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <h1 className="page-title">Services</h1>
        <button className="btn btn-primary btn-sm" onClick={() => setShowCreate(!showCreate)}>
          + Add Service
        </button>
      </div>

      {error && <div className="alert-error mb-4">{error}</div>}
      {msg && <div className="alert-success mb-4">{msg}</div>}

      {showCreate && (
        <form onSubmit={handleCreate} className="card mb-6 space-y-4">
          <h2 className="font-semibold">New service</h2>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="field-label">Slug *</label>
              <input
                className="field-input"
                required
                placeholder="xephon-foo"
                value={createForm.slug}
                onChange={(e) => setCreateForm((p) => ({ ...p, slug: e.target.value }))}
              />
            </div>
            <div>
              <label className="field-label">Name *</label>
              <input
                className="field-input"
                required
                placeholder="Xephon Foo"
                value={createForm.name}
                onChange={(e) => setCreateForm((p) => ({ ...p, name: e.target.value }))}
              />
            </div>
            <div>
              <label className="field-label">Base URL</label>
              <input
                className="field-input"
                placeholder="http://localhost:8000"
                value={createForm.base_url}
                onChange={(e) => setCreateForm((p) => ({ ...p, base_url: e.target.value }))}
              />
            </div>
            <div>
              <label className="field-label">Roles (comma-separated)</label>
              <input
                className="field-input"
                placeholder="foo:viewer, foo:editor"
                value={createForm.roles}
                onChange={(e) => setCreateForm((p) => ({ ...p, roles: e.target.value }))}
              />
            </div>
          </div>
          <div className="flex gap-2">
            <button type="submit" className="btn btn-primary btn-sm">Create</button>
            <button type="button" className="btn btn-ghost btn-sm" onClick={() => setShowCreate(false)}>
              Cancel
            </button>
          </div>
        </form>
      )}

      <div className="space-y-3">
        {services.map((svc) => (
          <div key={svc.slug} className="card">
            {editSlug === svc.slug ? (
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
                    <label className="field-label">Base URL</label>
                    <input
                      className="field-input"
                      value={editForm.base_url}
                      onChange={(e) => setEditForm((p) => ({ ...p, base_url: e.target.value }))}
                    />
                  </div>
                  <div className="col-span-2">
                    <label className="field-label">Roles (comma-separated)</label>
                    <input
                      className="field-input"
                      value={editForm.roles}
                      onChange={(e) => setEditForm((p) => ({ ...p, roles: e.target.value }))}
                    />
                  </div>
                </div>
                <div className="flex gap-2">
                  <button type="submit" className="btn btn-primary btn-sm">Save</button>
                  <button type="button" className="btn btn-ghost btn-sm" onClick={() => setEditSlug(null)}>
                    Cancel
                  </button>
                </div>
              </form>
            ) : (
              <div className="flex items-start justify-between gap-4">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold">{svc.name}</span>
                    <span className="badge badge-gray font-mono">{svc.slug}</span>
                    {svc.enabled ? (
                      <span className="badge badge-green">Enabled</span>
                    ) : (
                      <span className="badge badge-red">Disabled</span>
                    )}
                  </div>
                  {svc.base_url && (
                    <p className="text-gray-500 text-xs font-mono">{svc.base_url}</p>
                  )}
                  {svc.roles.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-1">
                      {svc.roles.map((r) => (
                        <span key={r} className="badge badge-purple">{r}</span>
                      ))}
                    </div>
                  )}
                </div>
                <div className="flex gap-2 shrink-0">
                  <button className="btn btn-ghost btn-sm" onClick={() => startEdit(svc)}>
                    Edit
                  </button>
                  <button
                    className={`btn btn-sm ${svc.enabled ? "btn-danger" : "btn-primary"}`}
                    onClick={() => toggleEnabled(svc)}
                  >
                    {svc.enabled ? "Disable" : "Enable"}
                  </button>
                </div>
              </div>
            )}
          </div>
        ))}
        {services.length === 0 && <div className="empty-state">No services configured.</div>}
      </div>
    </div>
  );
}
