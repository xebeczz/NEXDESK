import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * Flatten a FastAPI/pydantic error (which can be a string, an object, or an array
 * of `{type, loc, msg, input, ctx}` validation items) into a single readable string.
 * Never throws and never returns an object, so it is safe to pass to toast.error()
 * or render in JSX.
 */
export function extractErrorMessage(err: unknown, fallback = "Something went wrong"): string {
  const detail = (err as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail;
  if (typeof detail === "string") return detail || fallback;
  if (Array.isArray(detail)) {
    const parts: string[] = [];
    for (const item of detail) {
      if (item == null) continue;
      if (typeof item === "string") {
        parts.push(item);
        continue;
      }
      const message = (item as { msg?: unknown })?.msg ?? (item as { detail?: unknown })?.detail;
      if (typeof message === "string" && message) parts.push(message);
    }
    return parts.length ? parts.join("; ") : fallback;
  }
  if (detail && typeof detail === "object") {
    const message =
      (detail as { msg?: unknown })?.msg ?? (detail as { detail?: unknown })?.detail;
    if (typeof message === "string" && message) return message;
  }
  const networkMessage = (err as { message?: unknown })?.message;
  if (typeof networkMessage === "string" && networkMessage) return networkMessage;
  return fallback;
}

export function titleCase(value?: string | null): string {
  if (!value) return "—";
  return value
    .replace(/[_-]+/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

export function formatDate(value?: string | null): string {
  if (!value) return "—";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return "—";
  return d.toLocaleString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function formatRelative(value?: string | null): string {
  if (!value) return "—";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return "—";
  const diff = Date.now() - d.getTime();
  const mins = Math.round(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.round(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.round(hours / 24);
  if (days < 30) return `${days}d ago`;
  return d.toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" });
}

export function downloadBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

export function formatBytes(bytes?: number | null): string {
  if (!bytes || bytes === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB", "TB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
}

// New badge class names matching the design system
export const STATUS_BADGE = {
  open: "badge-primary",
  in_progress: "badge-warning",
  pending: "badge-info",
  resolved: "badge-success",
  closed: "badge-neutral",
} as const;

export const PRIORITY_BADGE = {
  low: "badge-neutral",
  medium: "badge-primary",
  high: "badge-warning",
  critical: "badge-danger",
} as const;

export const SLA_BADGE: Record<string, string> = {
  within_sla: "badge-success",
  at_risk: "badge-warning",
  breached: "badge-danger",
  ok: "badge-success",
  warning: "badge-warning",
  healthy: "badge-success",
  unhealthy: "badge-danger",
};

export const ROLE_BADGE = {
  admin: "badge-danger",
  user: "badge-primary",
} as const;