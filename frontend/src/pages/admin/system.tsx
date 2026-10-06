import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Activity, Users, Ticket as TicketIcon, Clock3, Calendar, Server, Database, BarChart3 } from "lucide-react";
import { adminApi } from "@/api/endpoints";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { formatRelative } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

export default function SystemPage() {
  const { data: health, isLoading: healthLoading } = useQuery({
    queryKey: ["admin", "system-health"],
    queryFn: adminApi.systemHealth,
  });
  const [auditPage, setAuditPage] = useState(1);
  const { data: audit, isLoading: auditLoading } = useQuery({
    queryKey: ["admin", "audit", auditPage],
    queryFn: () => adminApi.auditLogs({ page: auditPage, page_size: 20 }),
  });

  const uptimeH = health?.uptime_seconds != null
    ? Math.round(health.uptime_seconds / 3600)
    : null;

  interface StatItem {
    title: string;
    value: string;
    icon: any;
    color: string;
    bg: string;
    status?: string;
  }

  const statCards: StatItem[] = [
    {
      title: "API Status",
      value: healthLoading ? "..." : health?.status ?? "—",
      icon: Activity,
      color: "text-primary",
      bg: "bg-primary/10",
      status: health?.status === "healthy" ? "healthy" : health?.status === "degraded" ? "degraded" : "unknown",
    },
    {
      title: "Uptime",
      value: healthLoading ? "..." : uptimeH != null ? `${uptimeH}h` : "—",
      icon: Clock3,
      color: "text-success",
      bg: "bg-success/10",
    },
    {
      title: "Total Users",
      value: healthLoading ? "..." : String(health?.total_users ?? "—"),
      icon: Users,
      color: "text-info",
      bg: "bg-info/10",
    },
    {
      title: "Total Tickets",
      value: healthLoading ? "..." : String(health?.total_tickets ?? "—"),
      icon: TicketIcon,
      color: "text-warning",
      bg: "bg-warning/10",
    },
  ];

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="page-title">System</h1>
        <p className="page-subtitle">Health, workload, and audit trail</p>
      </div>

      {/* Health cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {statCards.map((stat) => (
          <Card key={stat.title} className="card-elevated">
            <CardContent className="flex items-center gap-4 p-5">
              <div className={cn("flex h-10 w-10 items-center justify-center rounded-lg", stat.bg, stat.color)}>
                <stat.icon className="h-5 w-5" />
              </div>
              <div className="min-w-0">
                <p className="text-xs font-medium text-text-muted uppercase tracking-wider">{stat.title}</p>
                <p className="text-lg font-bold text-text-primary truncate">{stat.value}</p>
                {stat.status && (
                  <Badge variant={stat.status === "healthy" ? "success" : stat.status === "degraded" ? "warning" : "neutral"} className="mt-1">
                    {stat.status}
                  </Badge>
                )}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Database/Engine info if available */}
      {health && !healthLoading && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <Card className="card-elevated">
            <CardContent className="flex items-center gap-4 p-5">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-info/10 text-info">
                <Database className="h-5 w-5" />
              </div>
              <div>
                <p className="text-xs font-medium text-text-muted uppercase tracking-wider">Database</p>
                <p className="text-lg font-bold text-text-primary">{health.db_status ?? "connected"}</p>
              </div>
            </CardContent>
          </Card>
          <Card className="card-elevated">
            <CardContent className="flex items-center gap-4 p-5">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-warning/10 text-warning">
                <Server className="h-5 w-5" />
              </div>
              <div>
                <p className="text-xs font-medium text-text-muted uppercase tracking-wider">Environment</p>
                <p className="text-lg font-bold text-text-primary">{health.environment ?? "production"}</p>
              </div>
            </CardContent>
          </Card>
          <Card className="card-elevated">
            <CardContent className="flex items-center gap-4 p-5">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-danger/10 text-danger">
                <Activity className="h-5 w-5" />
              </div>
              <div>
                <p className="text-xs font-medium text-text-muted uppercase tracking-wider">Load</p>
                <p className="text-lg font-bold text-text-primary">{health.load_average ?? "normal"}</p>
              </div>
            </CardContent>
          </Card>
          <Card className="card-elevated">
            <CardContent className="flex items-center gap-4 p-5">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 text-primary">
                <BarChart3 className="h-5 w-5" />
              </div>
              <div>
                <p className="text-xs font-medium text-text-muted uppercase tracking-wider">Version</p>
                <p className="text-lg font-bold text-text-primary">{health.version ?? "1.0.0"}</p>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Audit log */}
      <Card className="card-elevated">
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <Activity className="h-4 w-4" />
            Audit log
          </CardTitle>
          <CardDescription>Recent system activity and administrative actions</CardDescription>
        </CardHeader>
        <CardContent className="space-y-2 p-4">
          {auditLoading ? (
            <Skeleton className="h-24 w-full" />
          ) : audit?.items.length === 0 ? (
            <div className="text-center py-8 text-text-muted">
              <Calendar className="h-12 w-12 mx-auto mb-3 text-text-muted/30" />
              <p className="font-medium text-text-secondary">No audit entries</p>
              <p className="text-sm">Activity will appear here as users interact with the system</p>
            </div>
          ) : (
            <>
              {audit?.items.map((entry) => (
                <div key={entry.id} className="flex items-start gap-3 rounded-lg border border-border bg-surface-hover p-3 text-sm transition-colors hover:bg-surface-hover/80">
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary">
                    <Calendar className="h-4 w-4" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="flex items-center gap-2 flex-wrap">
                      <span className="font-medium text-text-primary">{entry.actor ?? "System"}</span>
                      <Badge variant="neutral" className="text-xs">
                        {entry.action.replace(/_/g, " ")}
                      </Badge>
                      {entry.entity_type && (
                        <span className="text-xs text-text-muted">· {entry.entity_type}</span>
                      )}
                    </p>
                    {entry.details && Object.keys(entry.details).length > 0 && (
                      <p className="text-xs text-text-muted mt-1 font-mono">
                        {JSON.stringify(entry.details)}
                      </p>
                    )}
                    <p className="text-xs text-text-muted mt-1">{formatRelative(entry.created_at)}</p>
                  </div>
                </div>
              ))}
              {audit && audit.pages > 1 && (
                <div className="flex items-center justify-between pt-2 border-t border-border">
                  <p className="text-xs text-text-muted">
                    Page {audit.page} of {audit.pages} · {audit.total} entries
                  </p>
                  <div className="flex gap-1">
                    <Button
                      variant="outline"
                      size="sm"
                      disabled={audit.page <= 1}
                      onClick={() => setAuditPage(audit.page - 1)}
                    >
                      Prev
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      disabled={audit.page >= audit.pages}
                      onClick={() => setAuditPage(audit.page + 1)}
                    >
                      Next
                    </Button>
                  </div>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}