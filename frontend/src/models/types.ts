export type UserRole = "admin" | "user";

export interface User {
  id: string;
  email: string;
  username: string;
  full_name: string;
  department?: string | null;
  role: UserRole;
  is_active: boolean;
  last_login_at?: string | null;
  created_at: string;
}

export type TicketStatus =
  | "open"
  | "in_progress"
  | "pending"
  | "resolved"
  | "closed";
export type TicketPriority = "low" | "medium" | "high" | "critical";
export type SlaStatus = "within_sla" | "warning" | "breached";

export interface Ticket {
  id: string;
  ticket_no: string;
  title: string;
  description: string;
  category: string;
  priority: TicketPriority;
  status: TicketStatus;
  department?: string | null;
  sla_status?: SlaStatus | null;
  sla_deadline?: string | null;
  ai_summary?: string | null;
  created_by_id: string;
  assigned_to_id?: string | null;
  resolution_notes?: string | null;
  resolved_at?: string | null;
  closed_at?: string | null;
  created_at: string;
  updated_at: string;
  created_by?: User | null;
  assigned_to?: User | null;
}

export interface TicketComment {
  id: number;
  content: string;
  created_at: string;
  user?: User | null;
}

export interface TicketActivity {
  id: number;
  action: string;
  field?: string | null;
  old_value?: string | null;
  new_value?: string | null;
  created_at: string;
  user?: User | null;
}

export interface TicketAttachment {
  id: string;
  filename: string;
  size: number;
  content_type: string;
  uploaded_at: string;
  uploader?: User | null;
}

export interface TicketDetail extends Ticket {
  comments: TicketComment[];
  activities: TicketActivity[];
  attachments: TicketAttachment[];
}

export interface TicketListPage {
  items: Ticket[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface ChatMessage {
  id: number;
  role: "user" | "assistant" | "system";
  content: string;
  intent?: string | null;
  created_at: string;
}

export interface ChatSession {
  id: string;
  title: string;
  message_count: number;
  created_at: string;
  updated_at: string;
}

export interface AiTicketDraft {
  id: string;
  title: string;
  description: string;
  category: string;
  priority: string;
  department?: string | null;
  confidence: number;
  intent?: string | null;
  status: string;
  created_at: string;
}

export interface Notification {
  id: string;
  type: string;
  title: string;
  message: string;
  ticket_id?: string | null;
  is_read: boolean;
  created_at: string;
}

export interface DashboardStats {
  total: number;
  open: number;
  in_progress: number;
  pending: number;
  resolved: number;
  closed: number;
  active: number;
  unresolved: number;
  high_priority: number;
  critical: number;
  avg_resolution_hours?: number | null;
  sla_compliance_percent?: number | null;
  sla_breached: number;
  sla_warning: number;
  tickets_today: number;
  tickets_this_week: number;
  tickets_this_month: number;
  top_department?: string | null;
  status_counts: Record<string, number>;
  priority_counts: Record<string, number>;
  sla_counts: Record<string, number>;
}

export interface CountPoint {
  [key: string]: string | number;
}

export interface TimePoint {
  date: string;
  count: number;
}

export interface MonthPoint {
  month: string;
  count: number;
}

export interface BreachedTicket {
  ticket_no: string;
  title: string;
  priority: string;
  deadline?: string | null;
  status: string;
}

export interface SystemHealth {
  status: string;
  uptime_seconds?: number | null;
  environment: string;
  db_status: string;
  db_query_ms?: number | null;
  total_users: number;
  total_tickets: number;
  active_tickets: number;
  pending_drafts: number;
  load_average?: string | number | null;
  version?: string | null;
}

export interface AuditEntry {
  id: number;
  actor?: string | null;
  action: string;
  entity_type?: string | null;
  entity_id?: string | null;
  details?: Record<string, unknown> | null;
  created_at: string;
}

export interface Analysis {
  intent: string;
  confidence: number;
  priority: string;
  category: string;
  department?: string | null;
  summary: string;
  should_create_ticket: boolean;
  sentiment?: string | null;
}

export interface SimilarTicket {
  ticket_id: string;
  ticket_no: string;
  title: string;
  description: string;
  category: string;
  priority: string;
  status: string;
  department?: string | null;
  created_at?: string | null;
  resolved_at?: string | null;
  closed_at?: string | null;
  resolution_notes?: string | null;
  ai_summary?: string | null;
  similarity: number;
  created_by?: User | null;
}

export interface SimilarTicketsResponse {
  similar_tickets: SimilarTicket[];
}
