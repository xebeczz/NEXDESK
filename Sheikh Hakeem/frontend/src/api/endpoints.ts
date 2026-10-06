import { api, getAccessToken } from "./client";
import type {
  AiTicketDraft,
  AuditEntry,
  BreachedTicket,
  ChatMessage,
  ChatSession,
  CountPoint,
  DashboardStats,
  MonthPoint,
  Notification,
  SimilarTicket,
  SimilarTicketsResponse,
  SystemHealth,
  Ticket,
  TicketActivity,
  TicketAttachment,
  TicketComment,
  TicketDetail,
  TicketListPage,
  TimePoint,
  User,
} from "@/models/types";

export interface ThemePreference {
  theme: "light" | "dark" | "system";
}

export interface NotificationPreferences {
  email_notifications: boolean;
  push_notifications: boolean;
  ticket_updates: boolean;
  ticket_assignments: boolean;
  mentions: boolean;
  comments: boolean;
  weekly_digest: boolean;
}

export interface SecuritySettings {
  two_factor_enabled: boolean;
  last_password_change: string | null;
}

export interface SettingsResponse {
  user: User;
  theme_preference: ThemePreference;
  notification_preferences: NotificationPreferences;
  security_settings: SecuritySettings;
}

export interface TwoFASetupResponse {
  secret: string;
  qr_code: string;
  uri: string;
}

export interface LoginResult {
  access_token: string;
  user: User;
}

export const authApi = {
  login: (identifier: string, password: string, role?: "admin" | "user") =>
    api
      .post<LoginResult>("/auth/login", { identifier, password, role })
      .then((r) => r.data),
  register: (payload: Record<string, unknown>) =>
    api.post<LoginResult>("/auth/register", payload).then((r) => r.data),
  me: () => api.get<User>("/auth/me").then((r) => r.data),
  logout: () => api.post("/auth/logout").then((r) => r.data),
  forgotPassword: (email: string) =>
    api.post("/auth/forgot-password", { email }).then((r) => r.data),
  resetPassword: (token: string, new_password: string) =>
    api
      .post("/auth/reset-password", { token, new_password })
      .then((r) => r.data),
};

export interface TicketQuery {
  page?: number;
  page_size?: number;
  search?: string;
  category?: string;
  priority?: string;
  status?: string;
  department?: string;
  created_by?: string;
  assigned_to?: string;
  sort_by?: string;
  sort_order?: string;
}

export const ticketApi = {
  list: (params: TicketQuery = {}) =>
    api.get<TicketListPage>("/tickets", { params }).then((r) => r.data),
  create: (data: Record<string, unknown>) =>
    api.post<Ticket>("/tickets", data).then((r) => r.data),
  get: (id: string) =>
    api.get<TicketDetail>(`/tickets/${id}`).then((r) => r.data),
  update: (id: string, data: Record<string, unknown>) =>
    api.put<TicketDetail>(`/tickets/${id}`, data).then((r) => r.data),
  delete: (id: string) => api.delete(`/tickets/${id}`).then((r) => r.data),
  changeStatus: (id: string, payload: { status: string; resolution_notes?: string }) =>
    api.post<TicketDetail>(`/tickets/${id}/status`, payload).then((r) => r.data),
  assign: (id: string, assigned_to_id: string) =>
    api.post<TicketDetail>(`/tickets/${id}/assign`, { assigned_to_id }).then((r) => r.data),
  transfer: (id: string, assigned_to_id: string) =>
    api.post<TicketDetail>(`/tickets/${id}/transfer`, { assigned_to_id }).then((r) => r.data),
  close: (id: string, resolution_notes?: string) =>
    api
      .post<TicketDetail>(`/tickets/${id}/close`, { resolution_notes })
      .then((r) => r.data),
  reopen: (id: string) =>
    api.post<TicketDetail>(`/tickets/${id}/reopen`).then((r) => r.data),
  activities: (id: string) =>
    api.get<TicketActivity[]>(`/tickets/${id}/activities`).then((r) => r.data),
  comments: (id: string) =>
    api.get<TicketComment[]>(`/tickets/${id}/comments`).then((r) => r.data),
  addComment: (id: string, content: string) =>
    api
      .post<TicketComment>(`/tickets/${id}/comments`, { content })
      .then((r) => r.data),
  upload: (id: string, file: File) => {
    const form = new FormData();
    form.append("file", file);
    return api
      .post<TicketAttachment>(`/tickets/${id}/attachments`, form)
      .then((r) => r.data);
  },
  download: (id: string, attachmentId: string) =>
    api.get(`/tickets/${id}/attachments/${attachmentId}/download`, {
      responseType: "blob",
    }),
  findSimilar: (data: {
    title: string;
    description: string;
    category?: string;
    priority?: string;
    department?: string;
    exclude_ticket_id?: string;
    threshold?: number;
    limit?: number;
  }) =>
    api.post<SimilarTicketsResponse>("/tickets/similar", data).then((r) => r.data),
};

export const dashboardApi = {
  stats: () => api.get<DashboardStats>("/dashboard/stats").then((r) => r.data),
  ticketsOverTime: (days = 30) =>
    api
      .get("/analytics/tickets-over-time", { params: { days } })
      .then((r) => r.data as { items: TimePoint[] }),
  monthlyTrends: (months = 12) =>
    api
      .get("/analytics/monthly-trends", { params: { months } })
      .then((r) => r.data as { items: MonthPoint[] }),
  priorityDistribution: () =>
    api
      .get("/analytics/priority-distribution")
      .then((r) => r.data as { items: CountPoint[] }),
  statusDistribution: () =>
    api
      .get("/analytics/status-distribution")
      .then((r) => r.data as { items: CountPoint[] }),
  departmentDistribution: () =>
    api
      .get("/analytics/department-distribution")
      .then((r) => r.data as { items: CountPoint[] }),
  sla: () =>
    api.get("/analytics/sla").then((r) => r.data as { items: CountPoint[] }),
  slaBreached: () =>
    api
      .get("/analytics/sla-breached")
      .then((r) => r.data as { items: BreachedTicket[] }),
};

export const chatApi = {
  sessions: () => api.get<ChatSession[]>("/chat/sessions").then((r) => r.data),
  createSession: () =>
    api.post<ChatSession>("/chat/sessions", {}).then((r) => r.data),
  messages: (sessionId: string) =>
    api
      .get<ChatMessage[]>(`/chat/sessions/${sessionId}/messages`)
      .then((r) => r.data),
  deleteSession: (sessionId: string) =>
    api.delete(`/chat/sessions/${sessionId}`).then((r) => r.data),
  clear: (sessionId: string) =>
    api.delete(`/chat/sessions/${sessionId}/messages`).then((r) => r.data),
  drafts: () => api.get<AiTicketDraft[]>("/chat/drafts").then((r) => r.data),
  confirmDraft: (draftId: string) =>
    api.post(`/chat/drafts/${draftId}/confirm`).then((r) => r.data),
  dismissDraft: (draftId: string) =>
    api.post(`/chat/drafts/${draftId}/dismiss`).then((r) => r.data),
  sendStream: (sessionId: string, message: string, onToken: (t: string) => void, onEvent: (ev: unknown) => void): Promise<void> =>
    new Promise((resolve, reject) => {
      const token = getAccessToken();
      fetch(`/api/v1/chat/sessions/${sessionId}/messages`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        credentials: "include",
        body: JSON.stringify({ message }),
      })
        .then(async (res) => {
          if (!res.ok || !res.body) {
            let detail = `HTTP ${res.status}`;
            try {
              const err = await res.json();
              detail = err.detail ?? detail;
            } catch {
              /* ignore */
            }
            reject(new Error(detail));
            return;
          }
          const reader = res.body.getReader();
          const decoder = new TextDecoder();
          let buffer = "";
          for (;;) {
            const { done, value } = await reader.read();
            if (done) break;
            buffer += decoder.decode(value, { stream: true });
            const parts = buffer.split("\n\n");
            buffer = parts.pop() ?? "";
            for (const part of parts) {
              const line = part.trim();
              if (!line.startsWith("data:")) continue;
              const payload = line.slice(5).trim();
              if (payload === "[DONE]") continue;
              try {
                const ev = JSON.parse(payload);
                if (ev.type === "token") {
                  onToken(ev.content ?? "");
                } else {
                  onEvent(ev);
                }
              } catch {
                /* skip malformed frame */
              }
            }
          }
          resolve();
        })
        .catch(reject);
    }),
};

export const adminApi = {
  users: () => api.get<User[]>("/admin/users").then((r) => r.data),
  createUser: (data: Record<string, unknown>) =>
    api.post<User>("/admin/users", data).then((r) => r.data),
  updateUser: (id: string, data: Record<string, unknown>) =>
    api.patch<User>(`/admin/users/${id}`, data).then((r) => r.data),
  systemHealth: () =>
    api.get<SystemHealth>("/admin/system-health").then((r) => r.data),
  auditLogs: (params: { page?: number; page_size?: number; action?: string } = {}) =>
    api
      .get("/admin/audit-logs", { params })
      .then((r) => r.data as { items: AuditEntry[]; total: number; page: number; page_size: number; pages: number }),
};

export const notificationApi = {
  list: () => api.get<Notification[]>("/notifications").then((r) => r.data),
  markRead: (id: string) =>
    api.post(`/notifications/${id}/read`).then((r) => r.data),
  markAllRead: () => api.post("/notifications/read-all").then((r) => r.data),
};

export type ReportType =
  | "summary"
  | "analytics"
  | "resolution"
  | "priority"
  | "monthly";

export const reportsApi = {
  download: (type: ReportType) =>
    api.get(`/reports/${type}`, { responseType: "blob" }),
  ticketPdf: (ticketId: string) =>
    api.get(`/tickets/${ticketId}/pdf`, { responseType: "blob" }),
};

export const settingsApi = {
  getSettings: () =>
    api.get<SettingsResponse>("/settings").then((r) => r.data),
  updateProfile: (data: { full_name: string; department: string | null; username: string; email: string }) =>
    api.patch<User>("/settings/profile", data).then((r) => r.data),
  changePassword: (current_password: string, new_password: string) =>
    api.post("/settings/password", { current_password, new_password }).then((r) => r.data),
  updateAppearance: (theme: "light" | "dark" | "system") =>
    api.patch<ThemePreference>("/settings/appearance", { theme }).then((r) => r.data),
  updateNotifications: (data: NotificationPreferences) =>
    api.patch<NotificationPreferences>("/settings/notifications", data).then((r) => r.data),
  getSecurity: () =>
    api.get<SecuritySettings>("/settings/security").then((r) => r.data),
  enable2FA: () =>
    api.post<TwoFASetupResponse>("/settings/security/2fa/enable").then((r) => r.data),
  verify2FA: (code: string) =>
    api.post("/settings/security/2fa/verify", { code }).then((r) => r.data),
  disable2FA: (code: string) =>
    api.post("/settings/security/2fa/disable", { code }).then((r) => r.data),
};
