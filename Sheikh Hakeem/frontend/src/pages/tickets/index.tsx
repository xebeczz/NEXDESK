import { useState } from "react";
import { keepPreviousData, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus } from "lucide-react";
import { ticketApi, type TicketQuery } from "@/api/endpoints";
import { TicketTable } from "@/components/tickets/ticket-table";
import { Button } from "@/components/ui/button";
import { TicketFormDialog } from "@/components/tickets/ticket-form";

export default function TicketsPage() {
  const queryClient = useQueryClient();
  const [filters, setFilters] = useState<{
    search?: string;
    status?: string;
    priority?: string;
    page?: number;
  }>({ page: 1 });
  const [createOpen, setCreateOpen] = useState(false);

  const query: TicketQuery = {
    page: filters.page ?? 1,
    page_size: 15,
    search: filters.search,
    status: filters.status,
    priority: filters.priority,
  };

  const { data, isLoading, isFetching } = useQuery({
    queryKey: ["tickets", query],
    queryFn: () => ticketApi.list(query),
    placeholderData: keepPreviousData,
  });

  const onFilters = (f: typeof filters) => setFilters((prev) => ({ ...prev, ...f }));

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="page-title">All Tickets</h1>
          <p className="page-subtitle">Search and manage all tickets</p>
        </div>
        <Button onClick={() => setCreateOpen(true)}>
          <Plus className="h-4 w-4" />
          New Ticket
        </Button>
      </div>

      <TicketTable data={data} isLoading={isLoading || isFetching} onFilters={onFilters} />

      <TicketFormDialog
        open={createOpen}
        onOpenChange={setCreateOpen}
        onSuccess={() => queryClient.invalidateQueries({ queryKey: ["tickets"] })}
      />
    </div>
  );
}