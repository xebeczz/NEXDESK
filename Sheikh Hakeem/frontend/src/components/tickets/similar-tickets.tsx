import { useState } from "react";
import {
  ExternalLink,
  CheckCircle2,
  XCircle,
  FileText,
  Lightbulb,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { SimilarTicket } from "@/models/types";

interface SimilarTicketsProps {
  tickets: SimilarTicket[];
  onSolved: () => void;
  currentTitle?: string;
  currentDescription?: string;
  currentCategory?: string;
  currentPriority?: string;
  currentDepartment?: string;
}

function similarityLabel(score: number): { text: string; color: string } {
  if (score >= 95) return { text: "Very Similar", color: "bg-emerald-500/10 text-emerald-600 border-emerald-500/30" };
  if (score >= 85) return { text: "Highly Similar", color: "bg-blue-500/10 text-blue-600 border-blue-500/30" };
  if (score >= 70) return { text: "Similar", color: "bg-amber-500/10 text-amber-600 border-amber-500/30" };
  return { text: "Related", color: "bg-muted text-muted-foreground border-border" };
}

export default function SimilarTickets({
  tickets,
  onSolved,
  currentTitle,
  currentDescription,
  currentCategory,
  currentPriority,
  currentDepartment,
}: SimilarTicketsProps) {
  const [solutionOpen, setSolutionOpen] = useState(false);
  const [selectedTicket, setSelectedTicket] = useState<SimilarTicket | null>(null);
  const [tried, setTried] = useState(false);

  const handleViewSolution = (ticket: SimilarTicket) => {
    setSelectedTicket(ticket);
    setSolutionOpen(true);
  };

  const handleSolved = () => {
    setTried(true);
    onSolved();
    setTimeout(() => {
      setSolutionOpen(false);
      setTried(false);
    }, 2000);
  };

  if (!tickets.length) {
    return (
      <Card className="p-4 space-y-2 border-dashed">
        <div className="flex items-center gap-2 text-sm font-semibold text-foreground">
          <FileText className="h-4 w-4 text-muted-foreground" />
          Similar Tickets
        </div>
        <p className="text-xs text-muted-foreground">No similar resolved ticket was found.</p>
      </Card>
    );
  }

  return (
    <>
      <Card className="p-4 space-y-3">
        <div className="flex items-center justify-between border-b border-border/60 pb-2">
          <div className="flex items-center gap-2 text-sm font-semibold text-foreground">
            <FileText className="h-4 w-4 text-primary" />
            Similar Tickets
          </div>
          <span className="text-[11px] text-muted-foreground">
            {tickets.length} found
          </span>
        </div>

        <div className="h-[calc(100vh-18rem)] overflow-y-auto">
          <div className="space-y-2">
            {tickets.map((ticket) => {
              const sim = similarityLabel(ticket.similarity);
              return (
                <div
                  key={ticket.ticket_id}
                  className="rounded-lg border border-border/70 bg-surface/60 p-3 space-y-1.5 hover:border-border transition-colors cursor-pointer"
                  onClick={() => handleViewSolution(ticket)}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-1.5 flex-wrap">
                        <span className="text-[11px] font-mono text-text-muted">#{ticket.ticket_no}</span>
                        <span className="text-xs font-semibold text-foreground truncate">{ticket.title}</span>
                      </div>
                      <div className="flex items-center gap-1.5 mt-1 flex-wrap">
                        <Badge variant="outline" className="text-[9px] h-4 px-1.5 capitalize">
                          {ticket.priority}
                        </Badge>
                        <Badge variant="outline" className="text-[9px] h-4 px-1.5 capitalize">
                          {ticket.status}
                        </Badge>
                      </div>
                    </div>
                    <Badge className={`shrink-0 text-[9px] h-5 px-1.5 border ${sim.color}`}>
                      {ticket.similarity}%
                    </Badge>
                  </div>

                  <p className="text-[11px] text-text-secondary leading-relaxed line-clamp-2">
                    {ticket.description}
                  </p>

                  {ticket.resolution_notes && (
                    <p className="text-[10px] text-text-muted line-clamp-1">
                      <span className="font-medium">Resolution:</span> {ticket.resolution_notes}
                    </p>
                  )}

                  <div className="flex items-center gap-1.5 pt-1">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleViewSolution(ticket);
                      }}
                      className="h-7 text-[11px] gap-1"
                    >
                      <ExternalLink className="h-3 w-3" />
                      View Solution
                    </Button>
                    <Button
                      size="sm"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleViewSolution(ticket);
                      }}
                      className="h-7 text-[11px] gap-1 bg-primary hover:bg-primary/90"
                    >
                      <Lightbulb className="h-3 w-3" />
                      Try
                    </Button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </Card>

      {selectedTicket && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={() => setSolutionOpen(false)} />
          <div className="relative w-full max-w-lg rounded-2xl border border-border bg-card shadow-2xl p-6 space-y-4 animate-scale-in">
            <div className="flex items-center justify-between">
              <h3 className="text-base font-bold text-foreground">Previous Solution</h3>
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8"
                onClick={() => setSolutionOpen(false)}
              >
                <XCircle className="h-4 w-4" />
              </Button>
            </div>

            <div className="space-y-3">
              <div className="rounded-lg bg-surface p-3 border border-border/60 space-y-1">
                <p className="text-[10px] font-medium uppercase tracking-wider text-text-muted">Previous Issue</p>
                <p className="text-sm font-semibold text-foreground">#{selectedTicket.ticket_no} — {selectedTicket.title}</p>
              </div>

              {selectedTicket.ai_summary && (
                <div className="rounded-lg bg-surface p-3 border border-border/60 space-y-1">
                  <p className="text-[10px] font-medium uppercase tracking-wider text-text-muted">Root Cause</p>
                  <p className="text-xs text-foreground/90">{selectedTicket.ai_summary}</p>
                </div>
              )}

              {selectedTicket.resolution_notes && (
                <div className="rounded-lg bg-surface p-3 border border-border/60 space-y-1">
                  <p className="text-[10px] font-medium uppercase tracking-wider text-text-muted">Previous Resolution</p>
                  <p className="text-xs text-foreground/90 whitespace-pre-wrap">{selectedTicket.resolution_notes}</p>
                </div>
              )}

              <div className="rounded-lg bg-surface p-3 border border-border/60 space-y-1">
                <p className="text-[10px] font-medium uppercase tracking-wider text-text-muted">Status</p>
                <span className="badge badge-success capitalize">{selectedTicket.status}</span>
              </div>
            </div>

            {!tried ? (
              <div className="space-y-3 pt-2">
                <p className="text-xs text-text-secondary font-medium">
                  Try the recommended steps above and check whether your issue is resolved.
                </p>
                <div className="flex items-center gap-2">
                  <Button
                    size="sm"
                    onClick={handleSolved}
                    className="flex-1 bg-emerald-600 hover:bg-emerald-700 text-white text-xs h-9"
                  >
                    <CheckCircle2 className="mr-1.5 h-4 w-4" />
                    Yes, Problem Solved
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => setSolutionOpen(false)}
                    className="flex-1 text-xs h-9"
                  >
                    <XCircle className="mr-1.5 h-4 w-4" />
                    Close
                  </Button>
                </div>
              </div>
            ) : (
              <div className="rounded-lg border border-emerald-500/30 bg-emerald-500/10 p-4 text-center space-y-2">
                <div className="flex items-center justify-center gap-2 text-emerald-600 font-bold text-sm">
                  <CheckCircle2 className="h-5 w-5" />
                  Problem Resolved
                </div>
                <p className="text-xs text-text-secondary">Glad we could help. No new ticket is required.</p>
              </div>
            )}
          </div>
        </div>
      )}
    </>
  );
}
