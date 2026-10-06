import { useEffect, useState } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  ArrowLeft,
  Paperclip,
  Send,
  Trash2,
  Download,
  UserPlus,
  RefreshCw,
  CheckCircle2,
  X,
  MessageSquare,
  Clock,
  User,
  Calendar,
  AlertTriangle,
} from "lucide-react";
import { ticketApi, adminApi } from "@/api/endpoints";
import { useAuth } from "@/providers/auth";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { StatusBadge, PriorityBadge, SlaBadge } from "@/components/tickets/ticket-badge";
import { formatDate, formatRelative, formatBytes, downloadBlob, extractErrorMessage } from "@/lib/utils";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from "@/components/ui/dialog";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { cn } from "@/lib/utils";
import SimilarTickets from "@/components/tickets/similar-tickets";

export default function TicketDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { user } = useAuth();

  const { data: ticket, isLoading } = useQuery({
    queryKey: ["ticket", id],
    queryFn: () => ticketApi.get(id!),
    enabled: !!id,
  });

  const { data: admins = [], isFetching: adminsLoading, isError: adminsError } = useQuery({
    queryKey: ["admin", "users"],
    queryFn: adminApi.users,
    enabled: user?.role === "admin",
    staleTime: 60_000,
    retry: 2,
    retryDelay: 400,
  });

  const { data: similarTickets = [] } = useQuery({
    queryKey: ["ticket", id, "similar"],
    queryFn: () =>
      ticketApi.findSimilar({
        title: ticket?.title || "",
        description: ticket?.description || "",
        category: ticket?.category || undefined,
        priority: ticket?.priority || undefined,
        department: ticket?.department || undefined,
        exclude_ticket_id: ticket?.id,
        threshold: 70,
        limit: 5,
      }).then((r) => r.similar_tickets),
    enabled: !!ticket && !!id && user?.role === "admin",
  });

  const [comment, setComment] = useState("");
  const [resolutionNotes, setResolutionNotes] = useState("");
  const [assignee, setAssignee] = useState("");

  // Seed the dropdown from the ticket's existing assignment once it loads.
  // The select is controlled by `assignee`, so without this an already-assigned
  // ticket would render with an empty trigger. The assigned admin id comes from
  // `assigned_to.id` (the API returns the assigned user object, not `assigned_to_id`).
  // We only sync when the stored id actually differs, so a live user selection is
  // never overwritten.
  const assignedId = ticket?.assigned_to?.id ?? ticket?.assigned_to_id ?? "";
  useEffect(() => {
    if (assignedId && assignedId !== assignee) {
      setAssignee(assignedId);
    }
  }, [assignedId]);
  const [closeOpen, setCloseOpen] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [busy, setBusy] = useState(false);

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ["ticket", id] });
    queryClient.invalidateQueries({ queryKey: ["tickets"] });
    queryClient.invalidateQueries({ queryKey: ["my-tickets"] });
  };

  if (isLoading) {
    return (
      <div className="space-y-4 animate-fade-in">
        <Skeleton className="h-8 w-64" />
        <div className="grid gap-4 lg:grid-cols-3">
          <Skeleton className="lg:col-span-2 h-80" />
          <Skeleton className="h-80" />
        </div>
        <Skeleton className="h-60" />
      </div>
    );
  }

  if (!ticket) {
    return (
      <div className="space-y-4 animate-fade-in">
        <Link to="/tickets" className="text-sm text-primary hover:underline flex items-center gap-1">
          <ArrowLeft className="h-4 w-4" />
          Back to tickets
        </Link>
        <div className="empty-state">
          <div className="empty-state-icon">
            <AlertTriangle className="h-8 w-8" />
          </div>
          <h3 className="empty-state-title">Ticket not found</h3>
          <p className="empty-state-description">This ticket may have been deleted or you don't have permission to view it.</p>
        </div>
      </div>
    );
  }

  const isAdmin = user?.role === "admin";
  const adminOptions = admins.filter((e) => e.role === "admin" && e.is_active);

  const addComment = async () => {
    if (!comment.trim()) return;
    setBusy(true);
    try {
      await ticketApi.addComment(ticket.id, comment);
      setComment("");
      invalidate();
    } catch (e: any) {
      toast.error(extractErrorMessage(e, "Failed to add comment"));
    } finally {
      setBusy(false);
    }
  };

  const changeStatus = async (status: string) => {
    setBusy(true);
    try {
      await ticketApi.changeStatus(ticket.id, { status });
      toast.success("Status updated");
      invalidate();
    } catch (e: any) {
      toast.error(extractErrorMessage(e, "Failed to update status"));
    } finally {
      setBusy(false);
    }
  };

  const assign = async () => {
    if (!assignee) return;
    setBusy(true);
    try {
      await ticketApi.assign(ticket.id, assignee);
      setAssignee("");
      toast.success("Ticket assigned");
      invalidate();
    } catch (e: any) {
      toast.error(extractErrorMessage(e, "Failed to assign"));
    } finally {
      setBusy(false);
    }
  };

  const close = async () => {
    setBusy(true);
    try {
      await ticketApi.close(ticket.id, resolutionNotes || undefined);
      setCloseOpen(false);
      setResolutionNotes("");
      toast.success("Ticket closed");
      invalidate();
    } catch (e: any) {
      toast.error(extractErrorMessage(e, "Failed to close"));
    } finally {
      setBusy(false);
    }
  };

  const reopen = async () => {
    setBusy(true);
    try {
      await ticketApi.reopen(ticket.id);
      toast.success("Ticket reopened");
      invalidate();
    } catch (e: any) {
      toast.error(extractErrorMessage(e, "Failed to reopen"));
    } finally {
      setBusy(false);
    }
  };

  const remove = async () => {
    setBusy(true);
    try {
      await ticketApi.delete(ticket.id);
      toast.success("Ticket deleted");
      navigate("/tickets");
    } catch (e: any) {
      toast.error(extractErrorMessage(e, "Failed to delete"));
    } finally {
      setBusy(false);
    }
  };

  const downloadAttachment = async (attId: string, filename: string) => {
    try {
      const res = await ticketApi.download(ticket.id, attId);
      downloadBlob(res.data as Blob, filename);
    } catch (e: any) {
      toast.error("Failed to download attachment");
    }
  };

  const uploadFile = async (file: File) => {
    setBusy(true);
    try {
      await ticketApi.upload(ticket.id, file);
      toast.success("Attachment uploaded");
      invalidate();
    } catch (e: any) {
      toast.error(extractErrorMessage(e, "Upload failed"));
    } finally {
      setBusy(false);
    }
  };

  const initials = (name?: string | null) => {
    if (!name) return "?";
    return name
      .split(" ")
      .slice(0, 2)
      .map((p) => p[0])
      .join("")
      .toUpperCase();
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-center gap-3">
          <Link to="/tickets" className="btn btn-ghost btn-icon p-2 rounded-lg hover:bg-sidebar-item-hover transition-colors">
            <ArrowLeft className="h-5 w-5" />
          </Link>
          <div>
            <h1 className="page-title">{ticket.title}</h1>
             <p className="font-mono text-xs text-text-muted">{ticket.ticket_no ?? `#${ticket.id}`}</p>
          </div>
        </div>
      </div>

      {/* Main content */}
      <div className="grid gap-4 lg:grid-cols-3">
        {/* Left: Details & Timeline */}
        <div className="lg:col-span-2 space-y-4">
          {/* Details Card */}
          <Card className="card-elevated">
            <CardHeader>
              <CardTitle className="text-base">Details</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Badges */}
              <div className="flex flex-wrap gap-2">
                <StatusBadge status={ticket.status} />
                <PriorityBadge priority={ticket.priority} />
                <SlaBadge status={ticket.sla_status} />
                <span className="badge badge-neutral">{ticket.category}</span>
                {ticket.department && (
                  <span className="badge badge-neutral">{ticket.department}</span>
                )}
              </div>

              {/* Description */}
              <div>
                <p className="text-xs font-medium text-text-muted uppercase tracking-wider mb-2">Description</p>
                <p className="whitespace-pre-wrap text-sm text-text-secondary leading-relaxed">{ticket.description}</p>
              </div>

              {/* Metadata grid */}
              <div className="grid grid-cols-2 gap-4 pt-2 border-t border-border">
                <div>
                  <p className="text-xs font-medium text-text-muted uppercase tracking-wider">Created by</p>
                  <div className="flex items-center gap-2 mt-1">
                    <Avatar className="h-8 w-8 bg-primary-muted text-primary">
                      <AvatarFallback>{initials(ticket.created_by?.full_name)}</AvatarFallback>
                    </Avatar>
                    <span className="text-sm text-text-secondary">{ticket.created_by?.full_name ?? ticket.created_by_id}</span>
                  </div>
                </div>
                <div>
                  <p className="text-xs font-medium text-text-muted uppercase tracking-wider">Assigned to</p>
                  <div className="flex items-center gap-2 mt-1">
                    {ticket.assigned_to ? (
                      <>
                        <Avatar className="h-8 w-8 bg-success-muted text-success">
                          <AvatarFallback>{initials(ticket.assigned_to.full_name)}</AvatarFallback>
                        </Avatar>
                        <span className="text-sm text-text-secondary">{ticket.assigned_to.full_name}</span>
                      </>
                    ) : (
                      <span className="text-sm text-text-muted">Unassigned</span>
                    )}
                  </div>
                </div>
                <div>
                  <p className="text-xs font-medium text-text-muted uppercase tracking-wider">Created</p>
                  <p className="text-sm text-text-secondary mt-1">{formatDate(ticket.created_at)}</p>
                </div>
                <div>
                  <p className="text-xs font-medium text-text-muted uppercase tracking-wider">SLA deadline</p>
                  <p className="text-sm text-text-secondary mt-1">{formatDate(ticket.sla_deadline)}</p>
                </div>
              </div>

              {/* Resolution notes */}
              {ticket.resolution_notes && (
                <div className="rounded-lg border border-border bg-surface-hover p-4">
                  <p className="text-xs font-medium text-text-muted uppercase tracking-wider mb-1">Resolution notes</p>
                  <p className="text-sm text-text-secondary">{ticket.resolution_notes}</p>
                </div>
              )}

              {/* Similar Previous Tickets for Admin */}
              {isAdmin && (
                <div className="pt-2">
                  <SimilarTickets
                    tickets={similarTickets}
                    onSolved={() => {}}
                    currentTitle={ticket.title}
                    currentDescription={ticket.description}
                    currentCategory={ticket.category}
                    currentPriority={ticket.priority}
                    currentDepartment={ticket.department || undefined}
                  />
                </div>
              )}
            </CardContent>
          </Card>

          {/* Activity Timeline */}
          <Card className="card-elevated">
            <CardHeader>
              <CardTitle className="text-base">Activity</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {(ticket.activities ?? []).slice().reverse().map((a) => (
                <div key={a.id} className="flex items-start gap-3 text-sm">
                  <div className="relative">
                    <span className="mt-1.5 h-2 w-2 shrink-0 rounded-full bg-primary/60" />
                    {a !== (ticket.activities ?? []).slice().reverse()[(ticket.activities ?? []).length - 1] && (
                      <span className="absolute left-1 top-4 bottom-0 w-0.5 bg-border" />
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="capitalize">
                      <strong className="text-text-primary">{a.user?.full_name ?? "System"}</strong>{" "}
                      <span className="text-text-secondary">{a.action.replace(/_/g, " ")}</span>
                    </p>
                    {a.new_value && (
                      <p className="text-xs text-text-muted mt-1">
                        {a.field ? `${a.field}: ` : ""}
                        {a.old_value ? `${a.old_value} → ` : ""}
                        <span className="font-medium text-text-primary">{a.new_value}</span>
                      </p>
                    )}
                    <p className="text-xs text-text-muted mt-1">{formatRelative(a.created_at)}</p>
                  </div>
                </div>
              ))}
              {!ticket.activities?.length && (
                <p className="text-sm text-text-muted text-center py-4">No activity yet.</p>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Right: Actions & Comments */}
        <div className="space-y-4">
          {/* Actions Card */}
          <Card className="card-elevated sticky top-20">
            <CardHeader>
              <CardTitle className="text-base">Actions</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {isAdmin && ticket.status === "open" && (
                <Button
                  variant="outline"
                  className="w-full justify-start gap-2"
                  onClick={() => changeStatus("in_progress")}
                  disabled={busy}
                >
                  <RefreshCw className="h-4 w-4" />
                  Mark in progress
                </Button>
              )}
              {isAdmin && ticket.status === "in_progress" && (
                <Button
                  variant="outline"
                  className="w-full justify-start gap-2"
                  onClick={() => changeStatus("pending")}
                  disabled={busy}
                >
                  <Clock className="h-4 w-4" />
                  Move to pending
                </Button>
              )}
              {ticket.status !== "closed" && ticket.status !== "resolved" && (
                <Button
                  variant="secondary"
                  className="w-full justify-start gap-2"
                  onClick={() => setCloseOpen(true)}
                  disabled={busy}
                >
                  <CheckCircle2 className="h-4 w-4" />
                  Resolve / Close
                </Button>
              )}
              {(ticket.status === "closed" || ticket.status === "resolved") && (
                <Button
                  variant="outline"
                  className="w-full justify-start gap-2"
                  onClick={reopen}
                  disabled={busy}
                >
                  <RefreshCw className="h-4 w-4" />
                  Reopen
                </Button>
              )}
              {isAdmin && (
                <div className="space-y-2 pt-2 border-t border-border">
                  <Label className="text-xs font-medium text-text-muted uppercase tracking-wider">Assign to admin</Label>
                  <div className="flex gap-2">
                    <Select value={assignee} onValueChange={setAssignee}>
                      <SelectTrigger className="w-full">
                        <SelectValue placeholder="Select admin" />
                      </SelectTrigger>
                      <SelectContent>
                        {adminsLoading ? (
                          <div className="px-2 py-1.5 text-sm text-text-muted">Loading admins...</div>
                        ) : adminOptions.length === 0 ? (
                          <div className="px-2 py-1.5 text-sm text-text-muted">
                            {adminsError ? "Couldn't load admins" : "No admin users available"}
                          </div>
                        ) : (
                          adminOptions.map((e) => (
                            <SelectItem key={e.id} value={e.id}>
                              {e.full_name}
                            </SelectItem>
                          ))
                        )}
                      </SelectContent>
                    </Select>
                    <Button variant="outline" size="icon" onClick={assign} disabled={!assignee || busy || adminsLoading}>
                      {busy ? <RefreshCw className="h-4 w-4 animate-spin" /> : <UserPlus className="h-4 w-4" />}
                    </Button>
                  </div>
                </div>
              )}
              {user?.role === "admin" && (
                <Button
                  variant="destructive"
                  className="w-full justify-start gap-2 mt-2"
                  onClick={() => setDeleteOpen(true)}
                  disabled={busy}
                >
                  <Trash2 className="h-4 w-4" />
                  Delete ticket
                </Button>
              )}
            </CardContent>
          </Card>

          {/* Comments & Attachments */}
          <Card className="card-elevated">
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <MessageSquare className="h-4 w-4" />
                Comments & Attachments
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Comments */}
              <div className="space-y-3">
                {(ticket.comments ?? []).map((c) => (
                  <div key={c.id} className="rounded-lg border border-border bg-surface-hover p-3">
                    <div className="flex items-center justify-between gap-2 mb-2">
                      <div className="flex items-center gap-2">
                        <Avatar className="h-7 w-7 bg-primary-muted text-primary">
                          <AvatarFallback>{initials(c.user?.full_name)}</AvatarFallback>
                        </Avatar>
                        <span className="font-medium text-text-primary text-sm">{c.user?.full_name ?? "User"}</span>
                      </div>
                      <span className="text-xs text-text-muted whitespace-nowrap">{formatRelative(c.created_at)}</span>
                    </div>
                    <p className="text-sm text-text-secondary whitespace-pre-wrap">{c.content}</p>
                  </div>
                ))}
                {!ticket.comments?.length && (
                  <p className="text-sm text-text-muted text-center py-4">No comments yet.</p>
                )}
              </div>

              {/* Add comment */}
              <div className="flex gap-2 pt-2 border-t border-border">
                <Input
                  value={comment}
                  onChange={(e) => setComment(e.target.value)}
                  placeholder="Add a comment…"
                  onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && (e.preventDefault(), addComment())}
                  className="flex-1"
                />
                <Button size="icon" onClick={addComment} disabled={busy || !comment.trim()} aria-label="Send comment">
                  <Send className="h-4 w-4" />
                </Button>
              </div>

              {/* Attachments */}
              <div className="space-y-2 pt-2 border-t border-border">
                {(ticket.attachments ?? []).map((att) => (
                  <div key={att.id} className="flex items-center justify-between rounded-lg border border-border bg-surface-hover px-3 py-2">
                    <div className="flex items-center gap-3 text-sm min-w-0">
                      <Paperclip className="h-4 w-4 text-text-muted shrink-0" />
                      <div className="min-w-0">
                        <span className="truncate block text-text-primary">{att.filename}</span>
                        <span className="text-xs text-text-muted">{formatBytes(att.size)}</span>
                      </div>
                    </div>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => downloadAttachment(att.id, att.filename)}
                      aria-label={`Download ${att.filename}`}
                    >
                      <Download className="h-4 w-4" />
                    </Button>
                  </div>
                ))}
                <Label htmlFor="attach" className="text-xs font-medium text-text-muted uppercase tracking-wider block">
                  Upload attachment
                </Label>
                <Input
                  id="attach"
                  type="file"
                  onChange={(e) => e.target.files?.[0] && uploadFile(e.target.files[0])}
                  disabled={busy}
                  className="mt-1"
                />
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Close dialog */}
      <Dialog open={closeOpen} onOpenChange={setCloseOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Resolve & Close Ticket</DialogTitle>
            <DialogDescription>
              Add resolution notes describing how this was resolved.
            </DialogDescription>
          </DialogHeader>
          <Textarea
            value={resolutionNotes}
            onChange={(e) => setResolutionNotes(e.target.value)}
            placeholder="Resolution notes…"
            rows={4}
            className="mt-4"
          />
          <DialogFooter>
            <Button variant="outline" onClick={() => setCloseOpen(false)}>
              Cancel
            </Button>
            <Button onClick={close} disabled={busy}>
              {busy && <span className="spinner h-4 w-4 mr-2" />}
              Close ticket
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete dialog */}
      <Dialog open={deleteOpen} onOpenChange={setDeleteOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Delete Ticket</DialogTitle>
            <DialogDescription>
              This permanently deletes the ticket and all its comments, attachments, and activity. This cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteOpen(false)}>
              Cancel
            </Button>
            <Button variant="destructive" onClick={remove} disabled={busy}>
              {busy && <span className="spinner h-4 w-4 mr-2" />}
              Delete
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}