import React from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import {
  Ticket,
  Clock,
  AlertTriangle,
  Activity,
  ShieldCheck,
  CalendarDays,
  Building2,
  CheckCircle2,
  TrendingUp,
  TrendingDown,
  FileText,
  User,
} from "lucide-react";
import { dashboardApi, ticketApi } from "@/api/endpoints";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { TicketTable } from "@/components/tickets/ticket-table";
import { StatusBadge, PriorityBadge } from "@/components/tickets/ticket-badge";
import { TicketTrendChart, MonthlyBarChart, DonutChart, StatusBarChart } from "@/components/charts/charts";
import { useAuth } from "@/providers/auth";
import { formatDate } from "@/lib/utils";
import type { DashboardStats, Ticket as TicketType, TicketListPage } from "@/models/types";

function StatCard({
  title,
  value,
  icon,
  hint,
  trend,
  accentColor,
}: {
  title: string;
  value?: number | string | null;
  icon: React.ReactNode;
  hint?: string;
  trend?: { value: number; label: string };
  accentColor?: string;
}) {
  return (
    <Card className="kpi-card card-elevated" style={{ '--kpi-accent': accentColor ?? 'var(--primary)' } as React.CSSProperties}>
      <CardContent className="p-5">
        <div className="flex items-start justify-between gap-4">
          <div className="min-w-0 flex-1">
            <p className="kpi-label">{title}</p>
            <p className="kpi-value mt-1">{value ?? "—"}</p>
            {hint && <p className="kpi-hint mt-1">{hint}</p>}
            {trend && (
              <div className="flex items-center gap-1 mt-2">
                {trend.value >= 0 ? (
                  <TrendingUp className="h-3 w-3 text-success" />
                ) : (
                  <TrendingDown className="h-3 w-3 text-destructive" />
                )}
                <span className={`text-xs font-medium ${trend.value >= 0 ? 'text-success' : 'text-destructive'}`}>
                  {trend.value >= 0 ? '+' : ''}{trend.value}% {trend.label}
                </span>
              </div>
            )}
          </div>
          <div className="kpi-icon shrink-0" style={{ background: `${accentColor ?? '#3B82F6'}15`, color: accentColor ?? '#3B82F6' }}>
            {React.isValidElement(icon) ? React.cloneElement(icon as React.ReactElement<{ className?: string }>, { className: "h-5 w-5" }) : icon}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export default function DashboardPage() {
  const { user } = useAuth();
  const isAdmin = user?.role === "admin";

  const { data: stats, isLoading } = useQuery<DashboardStats>({
    queryKey: ["dashboard", "stats", user?.id],
    queryFn: dashboardApi.stats,
    refetchInterval: 60_000,
  });

  // DEBUG: Log user and stats to console
  console.log("[DASHBOARD DEBUG] User:", user?.id, user?.full_name, "Role:", user?.role);
  console.log("[DASHBOARD DEBUG] Stats from API:", stats);
  console.log("[DASHBOARD DEBUG] IsAdmin:", isAdmin);
  const { data: trend } = useQuery({
    queryKey: ["analytics", "trend", 30],
    queryFn: () => dashboardApi.ticketsOverTime(30),
  });
  const { data: monthly } = useQuery({
    queryKey: ["analytics", "monthly", 12],
    queryFn: () => dashboardApi.monthlyTrends(12),
  });
  const { data: priority } = useQuery({
    queryKey: ["analytics", "priority"],
    queryFn: dashboardApi.priorityDistribution,
  });
  const { data: status } = useQuery({
    queryKey: ["analytics", "status"],
    queryFn: dashboardApi.statusDistribution,
  });
  const { data: dept } = useQuery({
    queryKey: ["analytics", "dept"],
    queryFn: dashboardApi.departmentDistribution,
  });
  const { data: sla } = useQuery({
    queryKey: ["analytics", "sla"],
    queryFn: dashboardApi.sla,
  });

  const { data: myTickets, isLoading: ticketsLoading } = useQuery<TicketListPage>({
    queryKey: ["dashboard", "my-tickets", isAdmin ? "all" : user?.id],
    queryFn: () => ticketApi.list({
      page: 1,
      page_size: 10,
      sort_by: "created_at",
      sort_order: "desc",
      ...(isAdmin ? {} : { created_by: user?.id }),
    }),
  });

  const priorityData = (priority?.items ?? []).map((p) => ({
    name: String(p.priority).replace("_", " "),
    value: Number(p.count),
  }));
  const statusData = (status?.items ?? []).map((s) => ({
    name: String(s.status).replace("_", " "),
    count: Number(s.count),
  }));
  const deptData = (dept?.items ?? []).map((d) => ({
    name: String(d.department),
    value: Number(d.count),
  }));
  const slaData = [
    { name: "Within SLA", count: Number(sla?.items?.find((i: any) => i.status === "within_sla")?.count ?? 0) },
    { name: "At risk", count: Number(sla?.items?.find((i: any) => i.status === "at_risk")?.count ?? 0) },
    { name: "Breached", count: Number(sla?.items?.find((i: any) => i.status === "breached")?.count ?? 0) },
  ];

  const totalTrend = stats?.tickets_this_week && stats?.total
    ? { value: Math.round(((stats.tickets_this_week / Math.max(1, stats.total - stats.tickets_this_week)) * 100)), label: "vs last week" }
    : undefined;

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Page Header */}
      <div className="page-header">
        <h1 className="page-title">
          {isAdmin ? "Admin Dashboard" : "My Dashboard"}
        </h1>
        <p className="page-subtitle">
          Welcome back, {user?.full_name}.
          {isAdmin
            ? " Here's what's happening across all tickets."
            : " Here are your tickets and activity."}
        </p>
      </div>

      {/* KPI Grid */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4 xl:grid-cols-5">
        <StatCard
          title="Total tickets"
          value={stats?.total}
          icon={<Ticket />}
          hint={isAdmin ? `${stats?.tickets_this_week ?? 0} this week` : undefined}
          trend={totalTrend}
          accentColor="#3B82F6"
        />
        <StatCard
          title="Open"
          value={stats?.open}
          icon={<Activity />}
          accentColor="#3B82F6"
        />
        <StatCard
          title="In Progress"
          value={stats?.in_progress}
          icon={<Activity />}
          accentColor="#F59E0B"
        />
        <StatCard
          title="Pending"
          value={stats?.pending}
          icon={<Clock />}
          accentColor="#06B6D4"
        />
        <StatCard
          title="Resolved"
          value={stats?.resolved}
          icon={<CheckCircle2 />}
          hint={isAdmin ? `${stats?.closed ?? 0} closed` : undefined}
          accentColor="#22C55E"
        />

        {isAdmin && (
          <>
            <StatCard
              title="High priority"
              value={stats?.high_priority}
              icon={<AlertTriangle />}
              hint={`${stats?.critical ?? 0} critical`}
              accentColor="#EF4444"
            />
            <StatCard
              title="SLA compliance"
              value={stats?.sla_compliance_percent != null ? `${stats.sla_compliance_percent}%` : "—"}
              icon={<ShieldCheck />}
              hint={`${stats?.sla_breached ?? 0} breached`}
              accentColor="#8B5CF6"
            />
            <StatCard
              title="Avg resolution"
              value={stats?.avg_resolution_hours != null ? `${stats.avg_resolution_hours}h` : "—"}
              icon={<Clock />}
              accentColor="#06B6D4"
            />
            <StatCard
              title="Today"
              value={stats?.tickets_today}
              icon={<CalendarDays />}
              accentColor="#6366F1"
            />
            <StatCard
              title="Top department"
              value={stats?.top_department}
              icon={<Building2 />}
              accentColor="#EC4899"
            />
          </>
        )}
      </div>

      {/* Admin-only charts row */}
      {isAdmin && (
        <>
          {/* Charts Row 1 */}
          <div className="grid gap-4 lg:grid-cols-2">
            <Card className="chart-container card-elevated">
              <CardHeader className="chart-header">
                <div>
                  <CardTitle className="chart-title">Ticket volume — last 30 days</CardTitle>
                  <CardDescription className="chart-subtitle">Daily created tickets</CardDescription>
                </div>
              </CardHeader>
              <CardContent>
                {isLoading ? (
                  <Skeleton className="h-[280px] w-full" />
                ) : (
                  <TicketTrendChart data={trend?.items ?? []} />
                )}
              </CardContent>
            </Card>

            <Card className="chart-container card-elevated">
              <CardHeader className="chart-header">
                <div>
                  <CardTitle className="chart-title">Monthly trends</CardTitle>
                  <CardDescription className="chart-subtitle">12-month ticket creation</CardDescription>
                </div>
              </CardHeader>
              <CardContent>
                <MonthlyBarChart data={monthly?.items ?? []} />
              </CardContent>
            </Card>
          </div>

          {/* Charts Row 2 */}
          <div className="grid gap-4 lg:grid-cols-2">
            <Card className="chart-container card-elevated">
              <CardHeader className="chart-header">
                <div>
                  <CardTitle className="chart-title">Priority distribution</CardTitle>
                  <CardDescription className="chart-subtitle">By priority level</CardDescription>
                </div>
              </CardHeader>
              <CardContent>
                <DonutChart data={priorityData} />
              </CardContent>
            </Card>

            <Card className="chart-container card-elevated">
              <CardHeader className="chart-header">
                <div>
                  <CardTitle className="chart-title">Status distribution</CardTitle>
                  <CardDescription className="chart-subtitle">By current status</CardDescription>
                </div>
              </CardHeader>
              <CardContent>
                <StatusBarChart data={statusData} />
              </CardContent>
            </Card>
          </div>

          {/* Charts Row 3 */}
          <div className="grid gap-4 lg:grid-cols-2">
            <Card className="chart-container card-elevated">
              <CardHeader className="chart-header">
                <div>
                  <CardTitle className="chart-title">Department breakdown</CardTitle>
                  <CardDescription className="chart-subtitle">Tickets by department</CardDescription>
                </div>
              </CardHeader>
              <CardContent>
                <DonutChart data={deptData} />
              </CardContent>
            </Card>

            <Card className="chart-container card-elevated">
              <CardHeader className="chart-header">
                <div>
                  <CardTitle className="chart-title">SLA status</CardTitle>
                  <CardDescription className="chart-subtitle">Compliance vs breached</CardDescription>
                </div>
              </CardHeader>
              <CardContent>
                <StatusBarChart data={slaData} />
              </CardContent>
            </Card>
          </div>
        </>
      )}

      {/* User-specific: My Ticket Trends + Recent Tickets */}
      {!isAdmin && (
        <div className="grid gap-4 lg:grid-cols-2">
          <Card className="chart-container card-elevated">
            <CardHeader className="chart-header">
              <div>
                <CardTitle className="chart-title">My status distribution</CardTitle>
                <CardDescription className="chart-subtitle">Your tickets by status</CardDescription>
              </div>
            </CardHeader>
            <CardContent>
              <StatusBarChart data={statusData} />
            </CardContent>
          </Card>

          <Card className="chart-container card-elevated">
            <CardHeader className="chart-header">
              <div>
                <CardTitle className="chart-title">My ticket trends</CardTitle>
                <CardDescription className="chart-subtitle">Last 30 days</CardDescription>
              </div>
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <Skeleton className="h-[280px] w-full" />
              ) : (
                <TicketTrendChart data={trend?.items ?? []} />
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {/* Recent Tickets Table */}
      <Card className="card-elevated">
        <CardHeader className="chart-header">
          <div>
            <CardTitle className="chart-title">
              {isAdmin ? "Recent Tickets" : "My Recent Tickets"}
            </CardTitle>
            <CardDescription className="chart-subtitle">
              {isAdmin ? "Latest tickets across the system" : "Your most recently created tickets"}
            </CardDescription>
          </div>
          <Button asChild size="sm" variant="outline">
            <Link to={isAdmin ? "/tickets" : "/my-tickets"}>
              <FileText className="h-4 w-4" /> View All
            </Link>
          </Button>
        </CardHeader>
        <CardContent>
          {!myTickets && !isAdmin && (
            <div className="text-center py-8">
              <User className="mx-auto h-12 w-12 text-muted-foreground/30 mb-3" />
              <h3 className="font-medium mb-1">No tickets yet</h3>
              <p className="text-sm text-muted-foreground mb-4">Create your first support ticket</p>
              <Link to="/my-tickets" className="inline-flex items-center gap-2 text-primary hover:underline">
                <Ticket className="h-4 w-4" /> Get started
              </Link>
            </div>
          )}
          {myTickets && myTickets.items.length > 0 && !isAdmin && (
            <div className="overflow-x-auto">
              <table className="table w-full">
                <thead>
                  <tr>
                    <th>Ticket No</th>
                    <th>Title</th>
                    <th>Status</th>
                    <th>Priority</th>
                    <th>Created</th>
                  </tr>
                </thead>
                <tbody>
                  {myTickets.items.slice(0, 10).map((t: TicketType) => (
                    <tr key={t.id} className="border-b transition-colors hover:bg-surface-hover">
                      <td className="px-4 py-3 font-mono text-xs text-text-muted">
                        <Link to={`/tickets/${t.id}`} className="hover:text-primary hover:underline transition-colors">
                          {t.ticket_no ?? `#${t.id}`}
                        </Link>
                      </td>
                      <td className="px-4 py-3">
                        <Link to={`/tickets/${t.id}`} className="font-medium text-text-primary hover:text-primary transition-colors">
                          {t.title}
                        </Link>
                      </td>
                      <td className="px-4 py-3">
                        <StatusBadge status={t.status} />
                      </td>
                      <td className="px-4 py-3">
                        <PriorityBadge priority={t.priority} />
                      </td>
                      <td className="px-4 py-3 text-sm text-text-secondary">
                        {formatDate(t.created_at)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          {isAdmin && (
            <TicketTable
              data={myTickets}
              isLoading={ticketsLoading}
              onFilters={() => {}}
            />
          )}
        </CardContent>
      </Card>
    </div>
  );
}
