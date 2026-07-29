export interface User {
  id: string;
  username: string;
  email: string;
  firstName: string;
  lastName: string;
  enabled: boolean;
  emailVerified: boolean;
}

export interface RealmRole {
  id: string;
  name: string;
  description: string;
}

export interface Service {
  slug: string;
  name: string;
  base_url: string;
  enabled: boolean;
  roles: string[];
  created_at: string;
  updated_at: string;
}

export interface ServiceHealthEntry {
  status: "up" | "down";
  checked_at: string;
  latency_ms: number | null;
  streak: number;
}

export interface Instance {
  id: string;
  name: string;
  type: "saas" | "private" | "enterprise";
  base_url: string;
  enabled_services: string[];
  health_status: string;
  health: Record<string, ServiceHealthEntry>;
  cms_url: string | null;
  pm_url: string | null;
  pim_url: string | null;
  erp_url: string | null;
  ai_url: string | null;
  created_at: string;
  updated_at: string;
}

export interface AuditLogEntry {
  id: string;
  actor_subject: string;
  actor_email: string;
  action: string;
  target_user_id: string | null;
  target_user_email: string | null;
  details: Record<string, unknown> | null;
  created_at: string;
}

export interface AuditLogPage {
  total: number;
  page: number;
  page_size: number;
  items: AuditLogEntry[];
}
