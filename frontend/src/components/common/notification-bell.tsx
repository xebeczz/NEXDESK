import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Bell, CheckCheck } from "lucide-react";
import { notificationApi } from "@/api/endpoints";
import { formatRelative } from "@/lib/utils";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Button } from "@/components/ui/button";

export function NotificationBell() {
  const queryClient = useQueryClient();
  const [open, setOpen] = useState(false);
  const { data: notifications = [] } = useQuery({
    queryKey: ["notifications"],
    queryFn: notificationApi.list,
    refetchInterval: 30_000,
    enabled: open,
  });

  const unread = notifications.filter((n) => !n.is_read).length;

  const markAll = async () => {
    await notificationApi.markAllRead();
    queryClient.invalidateQueries({ queryKey: ["notifications"] });
  };

  const items = notifications.slice(0, 12);

  return (
    <DropdownMenu open={open} onOpenChange={setOpen}>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="icon" className="relative">
          <Bell className="h-5 w-5" />
          {unread > 0 && (
            <span className="absolute right-1 top-1 flex h-4 w-4 items-center justify-center rounded-full bg-red-500 text-[10px] font-bold text-white">
              {unread > 9 ? "9+" : unread}
            </span>
          )}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-80">
        <div className="flex items-center justify-between pr-2">
          <DropdownMenuLabel>Notifications</DropdownMenuLabel>
          {unread > 0 && (
            <button
              onClick={markAll}
              className="flex items-center gap-1 text-xs text-primary hover:underline"
            >
              <CheckCheck className="h-3 w-3" /> Mark all read
            </button>
          )}
        </div>
        <DropdownMenuSeparator />
        {items.length === 0 && (
          <p className="px-3 py-6 text-center text-sm text-muted-foreground">
            No notifications yet.
          </p>
        )}
        {items.map((n) => (
          <DropdownMenuItem key={n.id} className="flex flex-col items-start gap-0.5">
            <span className={`text-sm ${n.is_read ? "text-muted-foreground" : "font-medium"}`}>
              {n.title}
            </span>
            <span className="text-xs text-muted-foreground">{n.message}</span>
            <span className="text-[10px] text-muted-foreground">
              {formatRelative(n.created_at)}
            </span>
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}