import { useState } from "react";
import { Link } from "react-router-dom";
import { Search, ChevronLeft, ChevronRight, Filter, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { StatusBadge, PriorityBadge, SlaBadge } from "@/components/tickets/ticket-badge";
import { formatDate } from "@/lib/utils";
import type { TicketListPage, Ticket } from "@/models/types";
import { cn } from "@/lib/utils";

export interface TicketFilters {
  search?: string;
  status?: string;
  priority?: string;
  page?: number;
}

interface Props {
  data?: TicketListPage;
  isLoading?: boolean;
  onFilters: (f: TicketFilters) => void;
}

export function TicketTable({ data, isLoading, onFilters }: Props) {
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState<string | undefined>(undefined);
  const [priority, setPriority] = useState<string | undefined>(undefined);

  const applyFilters = (overrides: Partial<TicketFilters>) => {
    onFilters({
      search: search.trim() || undefined,
      status: status,
      priority: priority,
      page: 1,
      ...overrides,
    });
  };

  const page = data?.page ?? 1;
  const pages = Math.max(1, data?.pages ?? 1);
  const total = data?.total ?? 0;

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="flex flex-col sm:flex-row sm:items-center gap-3 flex-wrap">
        <div className="relative flex-1 min-w-[200px] sm:max-w-md">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-muted" />
          <Input
            className="pl-10 h-10"
            placeholder="Search tickets…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && applyFilters({})}
          />
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          <Select value={status} onValueChange={(v) => { setStatus(v); applyFilters({ status: v || undefined }); }}>
            <SelectTrigger className="w-40 h-10 relative">
              <SelectValue placeholder="Status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="open">Open</SelectItem>
              <SelectItem value="in_progress">In progress</SelectItem>
              <SelectItem value="pending">Pending</SelectItem>
              <SelectItem value="resolved">Resolved</SelectItem>
              <SelectItem value="closed">Closed</SelectItem>
            </SelectContent>
          </Select>

          <Select value={priority} onValueChange={(v) => { setPriority(v); applyFilters({ priority: v || undefined }); }}>
            <SelectTrigger className="w-40 h-10">
              <SelectValue placeholder="Priority" />
              {/* Debug: temporary test element */}
              {/* <span style={{ color: 'red', position: 'absolute', left: '8px' }}>PRIORITY_TEST</span> */}
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="low">Low</SelectItem>
              <SelectItem value="medium">Medium</SelectItem>
              <SelectItem value="high">High</SelectItem>
              <SelectItem value="critical">Critical</SelectItem>
            </SelectContent>
          </Select>

          {(status || priority || search) && (
            <Button
              variant="ghost"
              size="sm"
              className="h-10 gap-1"
              onClick={() => {
                setSearch("");
                setStatus(undefined);
                setPriority(undefined);
                onFilters({ page: 1 });
              }}
            >
              <X className="h-3.5 w-3.5" />
              Clear
            </Button>
          )}
        </div>
      </div>

      {/* Table */}
      <div className="table-container">
        <div className="overflow-x-auto">
          <table className="table">
            <thead>
              <tr>
                <th className="px-4 py-3">Ticket</th>
                <th className="px-4 py-3">Title</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Priority</th>
                <th className="px-4 py-3">SLA</th>
                <th className="px-4 py-3">Requester</th>
                <th className="px-4 py-3">Assignee</th>
                <th className="px-4 py-3">Created</th>
              </tr>
            </thead>
            <tbody>
              {isLoading || !data ? (
                Array.from({ length: 6 }).map((_, i) => (
                  <tr key={i}>
                    <td colSpan={8} className="px-4 py-4">
                      <Skeleton className="h-5 w-full" />
                    </td>
                  </tr>
                ))
              ) : data.items.length === 0 ? (
                <tr>
                  <td colSpan={8} className="px-4 py-12 text-center">
                    <div className="flex flex-col items-center gap-3 text-text-muted">
                      <Filter className="h-12 w-12 text-text-muted/30" />
                      <span className="text-base font-medium text-text-secondary">No tickets found</span>
                      <span className="text-sm">Try adjusting your filters</span>
                    </div>
                  </td>
                </tr>
              ) : (
                data.items.map((t: Ticket) => (
                  <tr key={t.id} className="border-b transition-colors hover:bg-surface-hover">
                    <td className="px-4 py-3 font-mono text-xs text-text-muted">
                      <Link to={`/tickets/${t.id}`} className="hover:text-primary hover:underline transition-colors">
                        {t.ticket_no ?? `#${t.id}`}
                      </Link>
                    </td>
                    <td className="max-w-[300px] truncate px-4 py-3">
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
                    <td className="px-4 py-3">
                      <SlaBadge status={t.sla_status} />
                    </td>
                    <td className="px-4 py-3 text-text-secondary">{t.created_by?.full_name ?? "—"}</td>
                    <td className="px-4 py-3 text-text-secondary">{t.assigned_to?.full_name ?? "—"}</td>
                    <td className="px-4 py-3 text-xs text-text-muted">{formatDate(t.created_at)}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {pages > 1 && (
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 border-t p-4 bg-background-elevated/50">
            <div className="flex items-center gap-3 text-sm text-text-secondary flex-wrap">
              <span>Showing</span>
              <span className="font-medium text-text-primary">
                {((page - 1) * 20) + 1}
              </span>
              <span>to</span>
              <span className="font-medium text-text-primary">
                {Math.min(page * 20, total)}
              </span>
              <span>of</span>
              <span className="font-medium text-text-primary">{total}</span>
              <span>tickets</span>
            </div>
            <div className="flex items-center gap-1 pagination">
              <Button
                variant="outline"
                size="sm"
                disabled={page <= 1}
                onClick={() => onFilters({ page: page - 1 })}
                className="h-9 w-9 pagination-btn"
                aria-label="Previous page"
              >
                <ChevronLeft className="h-4 w-4" />
              </Button>
              {Array.from({ length: Math.min(pages, 5) }, (_, i) => {
                let pageNum: number;
                if (pages <= 5) {
                  pageNum = i + 1;
                } else if (page <= 3) {
                  pageNum = i + 1;
                } else if (page >= pages - 2) {
                  pageNum = pages - 4 + i;
                } else {
                  pageNum = page - 2 + i;
                }
                return (
                  <Button
                    key={pageNum}
                    variant={page === pageNum ? "default" : "ghost"}
                    size="sm"
                    onClick={() => onFilters({ page: pageNum })}
                    className={cn("h-9 w-9 pagination-btn", page === pageNum && 'active')}
                    aria-label={`Page ${pageNum}`}
                    aria-current={page === pageNum ? "page" : undefined}
                  >
                    {pageNum}
                  </Button>
                );
              })}
              <Button
                variant="outline"
                size="sm"
                disabled={page >= pages}
                onClick={() => onFilters({ page: page + 1 })}
                className="h-9 w-9 pagination-btn"
                aria-label="Next page"
              >
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}