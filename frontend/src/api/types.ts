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
