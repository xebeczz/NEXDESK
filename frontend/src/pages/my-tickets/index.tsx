import { useState } from "react";
import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { Plus } from "lucide-react";
import { ticketApi } from "@/api/endpoints";
import { TicketTable } from "@/components/tickets/ticket-table";
import { Button } from "@/components/ui/button";
import { TicketFormDialog } from "@/components/tickets/ticket-form";
import { useAuth } from "@/providers/auth";

export default function MyTicketsPage() {
  const { user } = useAuth();
  const [filters, setFilters] = useState<{
    search?: string;
    status?: string;
    priority?: string;
    page?: number;
  }>({ page: 1 });
  const [createOpen, setCreateOpen] = useState(false);

  const query = {
    page: filters.page ?? 1,
    page_size: 15,
    search: filters.search,
    status: filters.status,
    priority: filters.priority,
    created_by: user?.id,
  };

  const { data, isLoading, isFetching } = useQuery({
    queryKey: ["my-tickets", query],
    queryFn: () => ticketApi.list(query),
    placeholderData: keepPreviousData,
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">My Tickets</h1>
          <p className="text-sm text-muted-foreground">Tickets you created or were assigned</p>
        </div>
        <Button onClick={() => setCreateOpen(true)}>
          <Plus /> New Ticket
        </Button>
      </div>

      <TicketTable
        data={data}
        isLoading={isLoading || isFetching}
        onFilters={(f) => setFilters((prev) => ({ ...prev, ...f }))}
      />

      <TicketFormDialog open={createOpen} onOpenChange={setCreateOpen} />
    </div>
  );
}