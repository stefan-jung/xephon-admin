import axios from "axios";
import { keycloak } from "../auth/keycloak";
import type { AuditLogPage, RealmRole, Service, User } from "./types";

const baseURL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8004/api/v1";

const http = axios.create({ baseURL });

http.interceptors.request.use(async (config) => {
  await keycloak.updateToken(30);
  config.headers.Authorization = `Bearer ${keycloak.token}`;
  return config;
});

// ── Users ─────────────────────────────────────────────────────────────────────

export async function listUsers(search = "", first = 0, max = 50): Promise<User[]> {
  return (await http.get<User[]>("/users", { params: { search, first, max } })).data;
}

export async function getUser(id: string): Promise<User> {
  return (await http.get<User>(`/users/${id}`)).data;
}

export async function inviteUser(payload: {
  email: string;
  username: string;
  first_name?: string;
  last_name?: string;
}): Promise<User> {
  return (await http.post<User>("/users", payload)).data;
}

export async function updateUser(
  id: string,
  patch: { firstName?: string; lastName?: string; email?: string; enabled?: boolean },
): Promise<User> {
  return (await http.patch<User>(`/users/${id}`, patch)).data;
}

export async function disableUser(id: string): Promise<void> {
  await http.post(`/users/${id}/disable`);
}

export async function enableUser(id: string): Promise<void> {
  await http.post(`/users/${id}/enable`);
}

export async function resetPassword(id: string): Promise<void> {
  await http.post(`/users/${id}/reset-password`);
}

// ── Roles ─────────────────────────────────────────────────────────────────────

export async function listRealmRoles(): Promise<RealmRole[]> {
  return (await http.get<RealmRole[]>("/roles")).data;
}

export async function getUserRoles(userId: string): Promise<RealmRole[]> {
  return (await http.get<RealmRole[]>(`/roles/users/${userId}`)).data;
}

export async function assignRole(userId: string, roleName: string): Promise<void> {
  await http.post(`/roles/users/${userId}/${roleName}`);
}

export async function removeRole(userId: string, roleName: string): Promise<void> {
  await http.delete(`/roles/users/${userId}/${roleName}`);
}

// ── Services ──────────────────────────────────────────────────────────────────

export async function listServices(): Promise<Service[]> {
  return (await http.get<Service[]>("/services")).data;
}

export async function createService(payload: {
  slug: string;
  name: string;
  base_url?: string;
  enabled?: boolean;
  roles?: string[];
}): Promise<Service> {
  return (await http.post<Service>("/services", payload)).data;
}

export async function updateService(
  slug: string,
  patch: { name?: string; base_url?: string; enabled?: boolean; roles?: string[] },
): Promise<Service> {
  return (await http.patch<Service>(`/services/${slug}`, patch)).data;
}

export async function deleteService(slug: string): Promise<void> {
  await http.delete(`/services/${slug}`);
}

// ── Audit log ─────────────────────────────────────────────────────────────────

export async function listAuditLog(params: {
  page?: number;
  page_size?: number;
  action?: string;
  target_user_id?: string;
}): Promise<AuditLogPage> {
  return (await http.get<AuditLogPage>("/audit", { params })).data;
}
