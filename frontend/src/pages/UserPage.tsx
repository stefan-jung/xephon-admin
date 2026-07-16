import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import {
  assignRole,
  disableUser,
  enableUser,
  getUser,
  getUserRoles,
  listRealmRoles,
  removeRole,
  resetPassword,
} from "../api/client";
import type { RealmRole, User } from "../api/types";

export function UserPage() {
  const { userId } = useParams<{ userId: string }>();
  const [user, setUser] = useState<User | null>(null);
  const [allRoles, setAllRoles] = useState<RealmRole[]>([]);
  const [userRoles, setUserRoles] = useState<RealmRole[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [msg, setMsg] = useState<string | null>(null);

  const loadUser = () => {
    if (!userId) return;
    Promise.all([getUser(userId), listRealmRoles(), getUserRoles(userId)])
      .then(([u, all, assigned]) => {
        setUser(u);
        setAllRoles(all.filter((r) => !r.name.startsWith("default-roles")));
        setUserRoles(assigned);
      })
      .catch((err) => setError(String(err)));
  };

  useEffect(loadUser, [userId]);

  const hasRole = (name: string) => userRoles.some((r) => r.name === name);

  async function toggleRole(role: RealmRole) {
    try {
      if (hasRole(role.name)) {
        await removeRole(userId!, role.name);
        setMsg(`Removed role "${role.name}"`);
      } else {
        await assignRole(userId!, role.name);
        setMsg(`Assigned role "${role.name}"`);
      }
      loadUser();
    } catch (err) {
      setError(String(err));
    }
  }

  async function handleToggleEnabled() {
    if (!user) return;
    try {
      if (user.enabled) {
        await disableUser(user.id);
        setMsg("User disabled.");
      } else {
        await enableUser(user.id);
        setMsg("User enabled.");
      }
      loadUser();
    } catch (err) {
      setError(String(err));
    }
  }

  async function handleResetPassword() {
    if (!userId) return;
    try {
      await resetPassword(userId);
      setMsg("Password-reset email sent.");
    } catch (err) {
      setError(String(err));
    }
  }

  if (!user) return <div className="page-container text-gray-400">Loading…</div>;

  const displayName = [user.firstName, user.lastName].filter(Boolean).join(" ") || user.username;

  return (
    <div className="page-container space-y-6">
      <div className="page-header">
        <div>
          <h1 className="page-title">{displayName}</h1>
          <p className="text-gray-500 text-sm mt-1">{user.email}</p>
        </div>
        <div className="flex gap-2">
          <button className="btn btn-ghost btn-sm" onClick={handleResetPassword}>
            Send password reset
          </button>
          <button
            className={`btn btn-sm ${user.enabled ? "btn-danger" : "btn-primary"}`}
            onClick={handleToggleEnabled}
          >
            {user.enabled ? "Disable user" : "Enable user"}
          </button>
        </div>
      </div>

      {error && <div className="alert-error">{error}</div>}
      {msg && <div className="alert-success">{msg}</div>}

      <div className="card space-y-1">
        <h2 className="font-semibold mb-3">Details</h2>
        <div className="grid grid-cols-2 gap-x-8 gap-y-2 text-sm">
          <div className="text-gray-500">Username</div>
          <div>{user.username}</div>
          <div className="text-gray-500">Email</div>
          <div>{user.email}</div>
          <div className="text-gray-500">Email verified</div>
          <div>{user.emailVerified ? "Yes" : "No"}</div>
          <div className="text-gray-500">Status</div>
          <div>
            {user.enabled ? (
              <span className="badge badge-green">Active</span>
            ) : (
              <span className="badge badge-red">Disabled</span>
            )}
          </div>
          <div className="text-gray-500">ID</div>
          <div className="font-mono text-xs text-gray-400">{user.id}</div>
        </div>
      </div>

      <div className="card">
        <h2 className="font-semibold mb-4">Realm Roles</h2>
        <div className="flex flex-wrap gap-2">
          {allRoles.map((role) => {
            const assigned = hasRole(role.name);
            return (
              <button
                key={role.name}
                onClick={() => toggleRole(role)}
                className={`px-3 py-1.5 rounded-full text-xs font-medium border transition-colors cursor-pointer ${
                  assigned
                    ? "bg-[--color-brand] text-white border-[--color-brand]"
                    : "bg-white text-gray-600 border-gray-300 hover:border-[--color-brand] hover:text-[--color-brand]"
                }`}
              >
                {assigned ? "✓ " : "+ "}{role.name}
              </button>
            );
          })}
        </div>
        {allRoles.length === 0 && (
          <p className="text-gray-400 text-sm">No realm roles defined.</p>
        )}
      </div>
    </div>
  );
}
