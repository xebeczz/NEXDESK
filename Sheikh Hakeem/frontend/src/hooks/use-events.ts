import { useEffect, useRef } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { getAccessToken } from "@/api/client";

interface NotificationEvent {
  id: string;
  type: string;
  title: string;
  message: string;
  ticket_id?: string | null;
  is_read: boolean;
  created_at?: string | null;
}

interface StreamEvent {
  type: string;
  notification?: NotificationEvent;
  [key: string]: unknown;
}

const REFRESH_MAP: Record<string, string[]> = {
  ticket_created: ["tickets", "my-tickets", "notifications"],
  ticket_updated: ["tickets", "my-tickets", "notifications"],
  ticket_assigned: ["tickets", "my-tickets", "notifications"],
  ticket_closed: ["tickets", "my-tickets", "notifications"],
};

/** Abortable SSE connection to /api/v1/events with automatic reconnection. */
export function subscribeEvents(
  onEvent: (event: StreamEvent) => void,
  signal?: AbortSignal,
): () => void {
  let cancelled = false;
  let controller = new AbortController();
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  let attempt = 0;

  const cleanup = () => {
    cancelled = true;
    controller.abort();
    if (reconnectTimer) clearTimeout(reconnectTimer);
  };

  const connect = async () => {
    if (cancelled || signal?.aborted) return;
    controller = new AbortController();
    const own = controller.signal;
    try {
      const res = await fetch("/api/v1/events", {
        method: "GET",
        headers: {
          Accept: "text/event-stream",
          Authorization: getAccessToken() ? `Bearer ${getAccessToken()}` : "",
        },
        credentials: "include",
        signal: own,
      });
      if (!res.ok || !res.body) {
        throw new Error(`HTTP ${res.status}`);
      }
      attempt = 0;
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      for (;;) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const frames = buffer.split("\n\n");
        buffer = frames.pop() ?? "";
        for (const frame of frames) {
          const line = frame.trim();
          if (!line.startsWith("data:")) continue; // ignore heartbeat comments
          const payload = line.slice(5).trim();
          if (!payload) continue;
          try {
            onEvent(JSON.parse(payload) as StreamEvent);
          } catch {
            /* ignore malformed frame */
          }
        }
      }
    } catch {
      /* stream closed or aborted — schedule reconnect */
    } finally {
      if (!cancelled && !(signal?.aborted || own.aborted)) {
        const delay = Math.min(1000 * 2 ** attempt, 15_000);
        attempt += 1;
        reconnectTimer = setTimeout(connect, delay);
      }
    }
  };

  void connect();

  if (signal) {
    signal.addEventListener("abort", cleanup, { once: true });
  }
  return cleanup;
}

/** Keeps the SSE stream alive and reacts to events with toast + cache refresh. */
export function useEvents(): void {
  const queryClient = useQueryClient();
  const clientRef = useRef(queryClient);
  clientRef.current = queryClient;

  useEffect(() => {
    return subscribeEvents((event) => {
      if (event.type !== "notification" || !event.notification) return;
      const n = event.notification;
      const keys = REFRESH_MAP[n.type] ?? ["notifications"];
      for (const key of keys) {
        clientRef.current.invalidateQueries({ queryKey: [key] });
      }
      if (n.ticket_id) {
        clientRef.current.invalidateQueries({ queryKey: ["ticket", n.ticket_id] });
      }
      toast(n.title, { description: n.message });
    });
  }, []);
}