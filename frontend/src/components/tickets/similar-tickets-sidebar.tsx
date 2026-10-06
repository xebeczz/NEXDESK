import { useState } from "react";
import {
  ExternalLink,
  Lightbulb,
  FileText,
  CheckCircle2,
  XCircle,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { SimilarTicket } from "@/models/types";

interface SimilarTicketsInlineProps {
  tickets: SimilarTicket[];
  loading?: boolean;
  onRaiseTicket?: () => void;
}

function similarityLabel(score: number): { text: string; color: string } {
  if (score >= 95) return { text: "Very Similar", color: "bg-emerald-500/10 text-emerald-600 border-emerald-500/30" };
  if (score >= 85) return { text: "Highly Similar", color: "bg-blue-500/10 text-blue-600 border-blue-500/30" };
  if (score >= 70) return { text: "Similar", color: "bg-amber-500/10 text-amber-600 border-amber-500/30" };
  return { text: "Related", color: "bg-muted text-muted-foreground border-border" };
}

export default function SimilarTicketsInline({
  tickets,
  loading = false,
  onRaiseTicket,
}: SimilarTicketsInlineProps) {
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [solutionState, setSolutionState] = useState<Record<string, "idle" | "tried" | "resolved">>({});

  const handleToggle = (ticket: SimilarTicket) => {
    if (expandedId === ticket.ticket_id) {
      setExpandedId(null);
    } else {
      setExpandedId(ticket.ticket_id);
      setSolutionState((prev) => ({ ...prev, [ticket.ticket_id]: "idle" }));
    }
  };

  const handleTrySolution = (ticketId: string) => {
    setSolutionState((prev) => ({ ...prev, [ticketId]: "tried" }));
  };

  const handleSolved = (ticketId: string) => {
    setSolutionState((prev) => ({ ...prev, [ticketId]: "resolved" }));
  };

  if (loading) {
    return (
      <Card className="p-4 space-y-3">
        <div className="flex items-center gap-2 text-sm font-semibold text-foreground">
          <FileText className="h-4 w-4 text-primary" />
          Similar Tickets
        </div>
        <div className="space-y-2">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-24 rounded-lg bg-muted/50 animate-pulse" />
          ))}
        </div>
      </Card>
    );
  }

  if (!tickets.length) {
    return (
      <Card className="p-4 space-y-2 border-dashed">
        <div className="flex items-center gap-2 text-sm font-semibold text-foreground">
          <FileText className="h-4 w-4 text-muted-foreground" />
          Similar Tickets
        </div>
        <p className="text-xs text-muted-foreground">No similar tickets found.</p>
      </Card>
    );
  }

  return (
    <Card className="p-4 space-y-3">
      <div className="flex items-center justify-between border-b border-border/60 pb-2">
        <div className="flex items-center gap-2 text-sm font-semibold text-foreground">
          <FileText className="h-4 w-4 text-primary" />
          Similar Tickets
        </div>
        <span className="text-[11px] text-muted-foreground">
          We found similar previous tickets.
        </span>
      </div>

      <div className="space-y-2">
        {tickets.map((ticket) => {
          const sim = similarityLabel(ticket.similarity);
          const isExpanded = expandedId === ticket.ticket_id;
          const state = solutionState[ticket.ticket_id] || "idle";

          return (
            <div
              key={ticket.ticket_id}
              className="rounded-lg border border-border/70 bg-surface/60 overflow-hidden transition-colors"
            >
              <div className="p-3 space-y-2">
                <div className="flex items-start justify-between gap-2">
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-1.5 flex-wrap">
                      <span className="text-[11px] font-mono text-text-muted">#{ticket.ticket_no}</span>
                      <span className="text-xs font-semibold text-foreground truncate">{ticket.title}</span>
                    </div>
                    <div className="flex items-center gap-1.5 mt-1 flex-wrap">
                      <Badge variant="outline" className="text-[9px] h-4 px-1.5 capitalize">
                        {ticket.status}
                      </Badge>
                    </div>
                  </div>
                  <Badge className={`shrink-0 text-[9px] h-5 px-1.5 border ${sim.color}`}>
                    {ticket.similarity}%
                  </Badge>
                </div>

                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => handleToggle(ticket)}
                  className="w-full h-7 text-[11px] gap-1"
                >
                  <ExternalLink className="h-3 w-3" />
                  {isExpanded ? "Hide Solution" : "View Solution"}
                  {isExpanded ? <ChevronUp className="h-3 w-3 ml-auto" /> : <ChevronDown className="h-3 w-3 ml-auto" />}
                </Button>
              </div>

              {isExpanded && (
                <div className="px-3 pb-3 space-y-3 border-t border-border/40 pt-3">
                  <div className="space-y-1.5">
                    <p className="text-[10px] font-medium uppercase tracking-wider text-text-muted">Previous Issue</p>
                    <p className="text-xs text-foreground/90 font-medium">{ticket.title}</p>
                    <p className="text-[11px] text-text-secondary leading-relaxed">{ticket.description}</p>
                  </div>

                  {ticket.ai_summary && (
                    <div className="space-y-1.5">
                      <p className="text-[10px] font-medium uppercase tracking-wider text-text-muted">Root Cause</p>
                      <p className="text-[11px] text-foreground/90">{ticket.ai_summary}</p>
                    </div>
                  )}

                  {ticket.resolution_notes && (
                    <div className="space-y-1.5">
                      <p className="text-[10px] font-medium uppercase tracking-wider text-text-muted">Resolution</p>
                      <p className="text-[11px] text-foreground/90 whitespace-pre-wrap">{ticket.resolution_notes}</p>
                    </div>
                  )}

                  {state === "idle" && (
                    <Button
                      size="sm"
                      onClick={() => handleTrySolution(ticket.ticket_id)}
                      className="w-full h-8 text-xs gap-1.5 bg-primary hover:bg-primary/90"
                    >
                      <Lightbulb className="h-3.5 w-3.5" />
                      Try This Solution
                    </Button>
                  )}

                  {state === "tried" && (
                    <div className="space-y-2 pt-1">
                      <p className="text-xs text-text-secondary font-medium text-center">
                        Did this solution solve your problem?
                      </p>
                      <div className="flex items-center gap-2">
                        <Button
                          size="sm"
                          onClick={() => handleSolved(ticket.ticket_id)}
                          className="flex-1 bg-emerald-600 hover:bg-emerald-700 text-white text-xs h-8"
                        >
                          <CheckCircle2 className="mr-1 h-3.5 w-3.5" />
                          Yes, Problem Solved
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={onRaiseTicket}
                          className="flex-1 text-xs h-8 border-rose-500/40 text-rose-600 hover:bg-rose-500/10"
                        >
                          <XCircle className="mr-1 h-3.5 w-3.5 text-rose-500" />
                          No, Raise Ticket
                        </Button>
                      </div>
                    </div>
                  )}

                  {state === "resolved" && (
                    <div className="rounded-lg border border-emerald-500/30 bg-emerald-500/10 p-3 text-center space-y-2">
                      <div className="flex items-center justify-center gap-2 text-emerald-600 font-bold text-xs">
                        <CheckCircle2 className="h-4 w-4" />
                        Problem Solved
                      </div>
                      <p className="text-[11px] text-text-secondary">Great! The previous solution resolved your issue.</p>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => {
                          setExpandedId(null);
                          setSolutionState((prev) => ({ ...prev, [ticket.ticket_id]: "idle" }));
                        }}
                        className="h-7 text-xs"
                      >
                        Back to AI Assistant
                      </Button>
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </Card>
  );
}
