import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { inviteUser, listUsers } from "../api/client";
import type { User } from "../api/types";

function UserBadge({ user }: { user: User }) {
  return user.enabled ? (
    <span className="badge badge-green">Active</span>
  ) : (
    <span className="badge badge-red">Disabled</span>
  );
}

export function UsersPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [search, setSearch] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [showInvite, setShowInvite] = useState(false);
  const [inviteForm, setInviteForm] = useState({
    email: "",
    username: "",
    first_name: "",
    last_name: "",
  });
  const [inviteSuccess, setInviteSuccess] = useState<string | null>(null);

  const load = (q = search) => {
    listUsers(q, 0, 100)
      .then(setUsers)
      .catch((err) => setError(String(err)));
  };

  useEffect(() => {
    load();
  }, []);

  function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    load(search);
  }

  async function handleInvite(e: React.FormEvent) {
    e.preventDefault();
    try {
      const user = await inviteUser(inviteForm);
      setInviteSuccess(`Invited ${user.email} — password-set email sent.`);
      setShowInvite(false);
      setInviteForm({ email: "", username: "", first_name: "", last_name: "" });
      load();
    } catch (err: unknown) {
      setError(String(err));
    }
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <h1 className="page-title">Users</h1>
        <button className="btn btn-primary btn-sm" onClick={() => setShowInvite(!showInvite)}>
          + Invite User
        </button>
      </div>

      {error && <div className="alert-error mb-4">{error}</div>}
      {inviteSuccess && <div className="alert-success mb-4">{inviteSuccess}</div>}

      {showInvite && (
        <form onSubmit={handleInvite} className="card mb-6 space-y-4">
          <h2 className="font-semibold">Invite new user</h2>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="field-label">Email *</label>
              <input
                type="email"
                className="field-input"
                required
                value={inviteForm.email}
                onChange={(e) => setInviteForm((p) => ({ ...p, email: e.target.value }))}
              />
            </div>
            <div>
              <label className="field-label">Username *</label>
              <input
                className="field-input"
                required
                value={inviteForm.username}
                onChange={(e) => setInviteForm((p) => ({ ...p, username: e.target.value }))}
              />
            </div>
            <div>
              <label className="field-label">First name</label>
              <input
                className="field-input"
                value={inviteForm.first_name}
                onChange={(e) => setInviteForm((p) => ({ ...p, first_name: e.target.value }))}
              />
            </div>
            <div>
              <label className="field-label">Last name</label>
              <input
                className="field-input"
                value={inviteForm.last_name}
                onChange={(e) => setInviteForm((p) => ({ ...p, last_name: e.target.value }))}
              />
            </div>
          </div>
          <div className="flex gap-2">
            <button type="submit" className="btn btn-primary btn-sm">Send invite</button>
            <button type="button" className="btn btn-ghost btn-sm" onClick={() => setShowInvite(false)}>
              Cancel
            </button>
          </div>
        </form>
      )}

      <form onSubmit={handleSearch} className="flex gap-2 mb-4">
        <input
          className="field-input max-w-xs"
          placeholder="Search users…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <button type="submit" className="btn btn-ghost btn-sm">Search</button>
      </form>

      {users.length === 0 ? (
        <div className="empty-state">No users found.</div>
      ) : (
        <div className="card">
          <table className="data-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Username</th>
                <th>Email</th>
                <th>Status</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id}>
                  <td className="font-medium">
                    {u.firstName || u.lastName
                      ? `${u.firstName} ${u.lastName}`.trim()
                      : "—"}
                  </td>
                  <td className="text-gray-600">{u.username}</td>
                  <td className="text-gray-600">{u.email || "—"}</td>
                  <td><UserBadge user={u} /></td>
                  <td className="text-right">
                    <Link
                      to={`/users/${u.id}`}
                      className="btn btn-ghost btn-sm text-[--color-brand]"
                    >
                      Manage →
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
