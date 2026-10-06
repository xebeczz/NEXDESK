import { useState, useEffect } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { ticketApi } from "@/api/endpoints";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Spinner } from "@/components/common/loading-screen";
import { useAuth } from "@/providers/auth";
import { extractErrorMessage } from "@/lib/utils";

const CATEGORIES = [
  "General",
  "Email",
  "Network & VPN",
  "Hardware",
  "Software",
  "Security",
  "Identity & Access",
  "IT Operations",
];

export interface InitialTicketData {
  title?: string;
  description?: string;
  category?: string;
  priority?: string;
  department?: string;
}

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess?: () => void;
  initialData?: InitialTicketData | null;
}

export function TicketFormDialog({ open, onOpenChange, onSuccess, initialData }: Props) {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState({
    title: "",
    description: "",
    category: "General",
    priority: "medium",
  });

  useEffect(() => {
    if (open) {
      if (initialData) {
        setForm({
          title: initialData.title || "",
          description: initialData.description || "",
          category: initialData.category || "General",
          priority: (initialData.priority || "medium").toLowerCase(),
        });
      } else {
        setForm({ title: "", description: "", category: "General", priority: "medium" });
      }
    }
  }, [open, initialData]);

  const reset = () =>
    setForm({ title: "", description: "", category: "General", priority: "medium" });

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const created = await ticketApi.create(form);
      toast.success(`Ticket ${created.ticket_no ?? `#${created.id}`} created successfully.`);
      reset();
      onOpenChange(false);
      onSuccess?.();
      queryClient.invalidateQueries({ queryKey: ["tickets"] });
      queryClient.invalidateQueries({ queryKey: ["my-tickets"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard", "stats"] });
      queryClient.invalidateQueries({ queryKey: ["analytics"] });
    } catch (err: unknown) {
      toast.error(extractErrorMessage(err, "Failed to create ticket"));
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>New Ticket</DialogTitle>
          <DialogDescription>Describe the IT issue you're facing.</DialogDescription>
        </DialogHeader>
        <form onSubmit={submit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="title">Title</Label>
            <Input
              id="title"
              value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
              minLength={3}
              required
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="description">Description</Label>
            <Textarea
              id="description"
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              minLength={3}
              required
              rows={4}
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Category</Label>
              <Select value={form.category} onValueChange={(v) => setForm({ ...form, category: v })}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {CATEGORIES.map((c) => (
                    <SelectItem key={c} value={c}>
                      {c}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Priority</Label>
              <Select value={form.priority} onValueChange={(v) => setForm({ ...form, priority: v })}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="low">Low</SelectItem>
                  <SelectItem value="medium">Medium</SelectItem>
                  <SelectItem value="high">High</SelectItem>
                  <SelectItem value="critical">Critical</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          {user && user.department && (
            <p className="text-xs text-muted-foreground">
              Department: {user.department} · requester: {user.full_name}
            </p>
          )}
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={loading}>
              {loading && <Spinner />} Create Ticket
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}