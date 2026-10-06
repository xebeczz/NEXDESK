import { Badge, type BadgeProps } from "@/components/ui/badge";
import { STATUS_BADGE, PRIORITY_BADGE, SLA_BADGE, titleCase } from "@/lib/utils";
import type { TicketPriority, TicketStatus, SlaStatus } from "@/models/types";

export function StatusBadge({ status, ...props }: { status: TicketStatus } & BadgeProps) {
  return (
    <Badge className={STATUS_BADGE[status] as string} {...props}>
      {titleCase(status)}
    </Badge>
  );
}

export function PriorityBadge({ priority, ...props }: { priority: TicketPriority } & BadgeProps) {
  return (
    <Badge className={PRIORITY_BADGE[priority] as string} {...props}>
      {titleCase(priority)}
    </Badge>
  );
}

export function SlaBadge({ status, ...props }: { status?: string | null } & BadgeProps) {
  if (!status) return null;
  const badgeClass = SLA_BADGE[status] || "badge-neutral";
  return (
    <Badge className={badgeClass} {...props}>
      {status.replace("_", " ")}
    </Badge>
  );
}