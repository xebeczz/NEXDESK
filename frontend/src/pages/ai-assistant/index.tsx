import { useEffect, useRef, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import {
  Bot,
  Copy,
  Send,
  Trash2,
  Plus,
  Sparkles,
  CheckCircle2,
  ArrowLeft,
  XCircle,
  HelpCircle,
  Ticket as TicketIcon,
} from "lucide-react";
import { chatApi, ticketApi } from "@/api/endpoints";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { ChatMessage, Analysis, SimilarTicket } from "@/models/types";
import { formatRelative, titleCase, extractErrorMessage } from "@/lib/utils";
import { TicketFormDialog, type InitialTicketData } from "@/components/tickets/ticket-form";
import SimilarTicketsInline from "@/components/tickets/similar-tickets-sidebar";

export interface CommonIssueConfig {
  id: string;
  title: string;
  issueType: string;
  rootCause: string;
  possibleCauses: string[];
  priority: "Low" | "Medium" | "High" | "Critical";
  confidence: number;
  solutionSteps: string[];
  category: string;
  department: string;
}

export const COMMON_ISSUES_DATA: CommonIssueConfig[] = [
  {
    id: "vpn",
    title: "VPN Not Working",
    issueType: "Network / VPN",
    rootCause: "VPN configuration or authentication failure",
    possibleCauses: [
      "Incorrect VPN credentials",
      "VPN configuration issue",
      "Network connectivity problem",
      "VPN service unavailable",
    ],
    priority: "Low",
    confidence: 95,
    solutionSteps: [
      "Check internet connectivity.",
      "Verify VPN username and password.",
      "Restart the VPN application.",
      "Disconnect and reconnect the VPN.",
      "Restart the computer.",
      "If the problem continues, raise a ticket to the Network Team.",
    ],
    category: "Network & VPN",
    department: "Network Support",
  },
  {
    id: "server",
    title: "Server Down",
    issueType: "Server / Infrastructure",
    rootCause: "Server service unavailable or server connectivity failure",
    possibleCauses: [
      "Server service stopped",
      "Network connectivity failure",
      "Server overload",
      "Hardware failure",
    ],
    priority: "Critical",
    confidence: 97,
    solutionSteps: [
      "Check whether the server is reachable.",
      "Check network connectivity.",
      "Verify whether the server service is running.",
      "Check server health/logs.",
      "Restart the affected service if authorized.",
      "If still unavailable, raise a ticket to the Infrastructure Team.",
    ],
    category: "Network & VPN",
    department: "Infrastructure Team",
  },
  {
    id: "internet",
    title: "Internet Not Working",
    issueType: "Network Connectivity",
    rootCause: "Network connection or DNS configuration problem",
    possibleCauses: [
      "Router issue",
      "DNS issue",
      "Network adapter problem",
      "ISP/network outage",
    ],
    priority: "High",
    confidence: 94,
    solutionSteps: [
      "Check Wi-Fi/LAN connection.",
      "Disconnect and reconnect to the network.",
      "Restart the router if applicable.",
      "Check network adapter.",
      "Verify DNS settings.",
      "If the problem continues, raise a Network ticket.",
    ],
    category: "Network & VPN",
    department: "Network Support",
  },
  {
    id: "login",
    title: "Login Problem",
    issueType: "Account / Authentication",
    rootCause: "Authentication or account credential problem",
    possibleCauses: [
      "Incorrect username/password",
      "Account locked",
      "Expired password",
      "Authentication service issue",
    ],
    priority: "Medium",
    confidence: 96,
    solutionSteps: [
      "Verify username and password.",
      "Check whether Caps Lock is enabled.",
      "Try resetting the password.",
      "Check whether the account is locked.",
      "Contact the IT Support Team if the issue continues.",
    ],
    category: "Identity & Access",
    department: "IT Support Team",
  },
  {
    id: "email",
    title: "Email Not Working",
    issueType: "Email / Software",
    rootCause: "Email configuration or server synchronization problem",
    possibleCauses: [
      "Incorrect account configuration",
      "Network issue",
      "Mail server issue",
      "Storage limit exceeded",
    ],
    priority: "Medium",
    confidence: 93,
    solutionSteps: [
      "Check internet connectivity.",
      "Restart the email application.",
      "Check account configuration.",
      "Check mailbox storage.",
      "Try webmail if available.",
      "Raise an Email Support ticket if unresolved.",
    ],
    category: "Email",
    department: "Email Support",
  },
  {
    id: "printer",
    title: "Printer Problem",
    issueType: "Hardware / Peripheral",
    rootCause: "Printer connectivity, driver, or configuration problem",
    possibleCauses: [
      "Printer offline",
      "Paper/ink problem",
      "Driver issue",
      "Network connection problem",
    ],
    priority: "Medium",
    confidence: 92,
    solutionSteps: [
      "Check printer power.",
      "Check paper and ink/toner.",
      "Verify printer connection.",
      "Check whether the printer is online.",
      "Restart the printer.",
      "Reinstall/update the printer driver if required.",
      "Raise a Hardware ticket if unresolved.",
    ],
    category: "Hardware & Equipment",
    department: "Hardware Support",
  },
  {
    id: "slow",
    title: "System Slow",
    issueType: "System Performance",
    rootCause: "High resource usage or insufficient system resources",
    possibleCauses: [
      "Too many background applications",
      "Low RAM",
      "Low disk space",
      "Malware",
      "Too many startup programs",
    ],
    priority: "Low",
    confidence: 91,
    solutionSteps: [
      "Close unnecessary applications.",
      "Check Task Manager.",
      "Check available disk space.",
      "Disable unnecessary startup applications.",
      "Restart the computer.",
      "Contact IT Support if performance remains slow.",
    ],
    category: "Hardware",
    department: "IT Support",
  },
  {
    id: "password",
    title: "Password Issue",
    issueType: "Account / Security",
    rootCause: "Password expired, forgotten, or authentication failure",
    possibleCauses: [
      "Forgotten password",
      "Expired password",
      "Account locked",
      "Password policy violation",
    ],
    priority: "Low",
    confidence: 96,
    solutionSteps: [
      "Select 'Forgot Password' if available.",
      "Follow the password reset process.",
      "Create a new password according to company policy.",
      "Try logging in again.",
      "Contact IT Support if the account remains locked.",
    ],
    category: "Identity & Access",
    department: "IT Support",
  },
];

function findMatchingCommonIssue(text: string): CommonIssueConfig | null {
  const lower = text.toLowerCase().trim();
  if (lower.includes("vpn")) return COMMON_ISSUES_DATA.find((i) => i.id === "vpn") || null;
  if (lower.includes("server") || lower.includes("host down") || lower.includes("system down"))
    return COMMON_ISSUES_DATA.find((i) => i.id === "server") || null;
  if (
    lower.includes("internet") ||
    lower.includes("wifi") ||
    lower.includes("wi-fi") ||
    lower.includes("network down") ||
    lower.includes("no net")
  )
    return COMMON_ISSUES_DATA.find((i) => i.id === "internet") || null;
  if (
    lower.includes("login") ||
    lower.includes("log in") ||
    lower.includes("can't sign in") ||
    lower.includes("sign in")
  )
    return COMMON_ISSUES_DATA.find((i) => i.id === "login") || null;
  if (lower.includes("email") || lower.includes("outlook") || lower.includes("mail"))
    return COMMON_ISSUES_DATA.find((i) => i.id === "email") || null;
  if (lower.includes("printer") || lower.includes("print") || lower.includes("spooler"))
    return COMMON_ISSUES_DATA.find((i) => i.id === "printer") || null;
  if (lower.includes("slow") || lower.includes("lag") || lower.includes("freez"))
    return COMMON_ISSUES_DATA.find((i) => i.id === "slow") || null;
  if (lower.includes("password") || lower.includes("pass word") || lower.includes("reset pass"))
    return COMMON_ISSUES_DATA.find((i) => i.id === "password") || null;

  return null;
}

interface DraftEvent {
  id: string;
  title: string;
  category: string;
  priority: string;
  department?: string | null;
  confidence: number;
  intent?: string | null;
  description?: string;
}

export default function AiAssistantPage() {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [draft, setDraft] = useState<DraftEvent | null>(null);

  // Selected Common Issue Diagnosis State
  const [selectedIssue, setSelectedIssue] = useState<CommonIssueConfig | null>(null);
  const [issueState, setIssueState] = useState<"diagnosing" | "solved" | "create_ticket">("diagnosing");

  // Similar tickets state
  const [similarTickets, setSimilarTickets] = useState<SimilarTicket[]>([]);
  const [loadingSimilar, setLoadingSimilar] = useState(false);

  // Ticket Form Dialog Modal State
  const [ticketDialogOpen, setTicketDialogOpen] = useState(false);
  const [prefillTicketData, setPrefillTicketData] = useState<InitialTicketData | null>(null);

  const scrollRef = useRef<HTMLDivElement>(null);
  const assistantIdxRef = useRef(-1);

  const { data: sessions = [] } = useQuery({
    queryKey: ["chat", "sessions"],
    queryFn: chatApi.sessions,
  });

  const { data: drafts = [] } = useQuery({
    queryKey: ["chat", "drafts"],
    queryFn: chatApi.drafts,
    refetchInterval: 15_000,
  });

  useEffect(() => {
    scrollRef.current?.scrollTo({
      top: scrollRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [messages, analysis, draft, streaming, selectedIssue, issueState, similarTickets]);

  const fetchSimilarTickets = async (title: string, description: string, category?: string, priority?: string) => {
    setLoadingSimilar(true);
    try {
      const res = await ticketApi.findSimilar({
        title,
        description,
        category,
        priority,
        threshold: 70,
        limit: 5,
      });
      setSimilarTickets(res.similar_tickets);
    } catch {
      setSimilarTickets([]);
    } finally {
      setLoadingSimilar(false);
    }
  };

  useEffect(() => {
    if (selectedIssue) {
      fetchSimilarTickets(selectedIssue.title, selectedIssue.title + " " + selectedIssue.rootCause, selectedIssue.category, selectedIssue.priority || undefined);
    } else if (analysis && !selectedIssue) {
      const lastUserMsg = messages.filter((m) => m.role === "user").pop();
      if (lastUserMsg) {
        fetchSimilarTickets(lastUserMsg.content || "", lastUserMsg.content || "", analysis.category, analysis.priority || undefined);
      }
    } else {
      setSimilarTickets([]);
    }
  }, [selectedIssue, analysis, messages]);

  const selectSession = async (sid: string) => {
    setSessionId(sid);
    setAnalysis(null);
    setDraft(null);
    setSelectedIssue(null);
    setIssueState("diagnosing");
    try {
      const msgs = await chatApi.messages(sid);
      setMessages(msgs);
    } catch {
      setMessages([]);
    }
  };

  const newSession = async () => {
    if (streaming) return;
    const s = await chatApi.createSession();
    if (!s?.id) {
      toast.error("Could not start an AI session. Please sign in and try again.");
      return;
    }
    queryClient.invalidateQueries({ queryKey: ["chat", "sessions"] });
    await selectSession(s.id);
  };

  const resetToCommonIssues = () => {
    setSelectedIssue(null);
    setIssueState("diagnosing");
  };

  const handleIssueClick = (issue: CommonIssueConfig) => {
    setSelectedIssue(issue);
    setIssueState("diagnosing");
  };

  const handleSolveClick = () => {
    setIssueState("solved");
  };

  const handleRaiseTicketClick = () => {
    if (!selectedIssue) return;
    const prefill = {
      title: selectedIssue.title,
      description: `User reported that ${selectedIssue.title.toLowerCase()} is occurring. AI analysis identified a possible ${selectedIssue.rootCause.toLowerCase()} issue.\n\nIssue Type: ${selectedIssue.issueType}\nPriority: ${selectedIssue.priority}\nRoot Cause: ${selectedIssue.rootCause}`,
      category: selectedIssue.category,
      issueType: selectedIssue.issueType,
      priority: selectedIssue.priority.toLowerCase(),
      department: selectedIssue.department,
    };
    // Single source of truth for the AI-derived ticket data. Persist it so the
    // Create Ticket page can always recover title/description/category/priority/
    // department, even if router navigation state is ever dropped.
    try {
      sessionStorage.setItem("itdesk.ticketPrefill", JSON.stringify(prefill));
    } catch {
      /* storage unavailable — router state below still carries it */
    }
    console.debug("[AI Assistant] Navigating to create-ticket with prefill:", prefill);
    navigate("/create-ticket", {
      state: {
        prefill,
      },
    });
  };

  const send = async () => {
    const text = input.trim();
    if (!text || streaming) return;

    // Check if input matches one of the 8 common issues
    const match = findMatchingCommonIssue(text);
    if (match) {
      setInput("");
      setSelectedIssue(match);
      setIssueState("diagnosing");
      return;
    }

    // Otherwise, clear selected issue view and stream LLM response
    setSelectedIssue(null);
    setInput("");
    setAnalysis(null);
    setDraft(null);

    let sid = sessionId;
    if (!sid) {
      const s = await chatApi.createSession();
      if (!s?.id) {
        toast.error("Could not start an AI session. Please sign in and try again.");
        return;
      }
      sid = s.id;
      setSessionId(s.id);
      queryClient.invalidateQueries({ queryKey: ["chat", "sessions"] });
    }

    setMessages((prev) => [
      ...prev,
      {
        id: Date.now(),
        role: "user",
        content: text,
        intent: null,
        created_at: new Date().toISOString(),
      },
      {
        id: Date.now() + 1,
        role: "assistant",
        content: "",
        intent: null,
        created_at: new Date().toISOString(),
      },
    ]);
    setStreaming(true);
    const targetIdx = messages.length + 1;
    assistantIdxRef.current = targetIdx;

    try {
      await chatApi.sendStream(
        sid,
        text,
        (token) => {
          setMessages((prev) => {
            const next = [...prev];
            const last = next[next.length - 1];
            if (last && last.role === "assistant") {
              next[next.length - 1] = {
                ...last,
                content: last.content + token,
              };
            }
            return next;
          });
        },
        (ev) => {
          const e = ev as { type: string; analysis?: Analysis; draft?: DraftEvent };
          if (e.type === "analysis" && e.analysis) setAnalysis(e.analysis);
          if (e.type === "draft" && e.draft) {
            setDraft(e.draft);
            queryClient.invalidateQueries({ queryKey: ["chat", "drafts"] });
          }
        },
      );
    } catch (err: any) {
      const message = err instanceof Error ? err.message : "Failed to send message";
      toast.error(message);
      setMessages((prev) => {
        if (prev.length === 0) return prev;
        const last = prev[prev.length - 1];
        if (last?.role === "assistant" && !last.content) {
          return [
            ...prev.slice(0, -1),
            {
              ...last,
              content: "I'm sorry, I couldn't generate a response. Please try again.",
            },
          ];
        }
        return prev;
      });
    } finally {
      setStreaming(false);
      queryClient.invalidateQueries({ queryKey: ["chat", "sessions"] });
    }
  };

  const clearChat = async () => {
    if (!sessionId || !window.confirm("Clear this conversation?")) return;
    await chatApi.clear(sessionId);
    setMessages([]);
    setAnalysis(null);
    setDraft(null);
    setSelectedIssue(null);
    setIssueState("diagnosing");
    queryClient.invalidateQueries({ queryKey: ["chat", "sessions"] });
  };

  const deleteCurrentSession = async () => {
    if (!sessionId || !window.confirm("Delete this conversation?")) return;
    await chatApi.deleteSession(sessionId);
    setSessionId(null);
    setMessages([]);
    setAnalysis(null);
    setDraft(null);
    setSelectedIssue(null);
    setIssueState("diagnosing");
    queryClient.invalidateQueries({ queryKey: ["chat", "sessions"] });
  };

  const confirmDraft = async (draftId: string) => {
    try {
      await chatApi.confirmDraft(draftId);
      toast.success("Ticket created from recommendation");
      setDraft(null);
      setAnalysis(null);
      queryClient.invalidateQueries({ queryKey: ["chat", "drafts"] });
    } catch (e: any) {
      toast.error(extractErrorMessage(e, "Failed to confirm"));
    }
  };

  const dismissDraft = async (draftId: string) => {
    try {
      await chatApi.dismissDraft(draftId);
      setDraft(null);
      setAnalysis(null);
      queryClient.invalidateQueries({ queryKey: ["chat", "drafts"] });
    } catch (e: any) {
      toast.error(extractErrorMessage(e, "Failed to dismiss"));
    }
  };

  return (
    <div className="w-full">
      {/* Modal Dialog for Pre-filled Ticket Creation */}
      <TicketFormDialog
        open={ticketDialogOpen}
        onOpenChange={setTicketDialogOpen}
        initialData={prefillTicketData}
        onSuccess={() => {
          setSelectedIssue(null);
          setIssueState("diagnosing");
        }}
      />

      <Card className="flex h-[calc(100vh-7rem)] overflow-hidden bg-background">
        {/* Main Content Area */}
        <div className="flex-1 flex flex-col min-w-0">
          {/* Header */}
          <div className="flex items-center justify-between border-b px-4 py-3 bg-card">
            <div className="flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10 text-primary">
                <Bot className="h-5 w-5" />
              </div>
              <div>
                <span className="font-semibold text-foreground flex items-center gap-1.5 text-sm">
                  AI Assistant
                  <Sparkles className="h-3.5 w-3.5 text-amber-500" />
                </span>
                <p className="text-[11px] text-muted-foreground">Automated IT issue diagnosis & support</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              {selectedIssue && (
                <Button variant="outline" size="sm" onClick={resetToCommonIssues} className="h-8 text-xs font-medium">
                  <ArrowLeft className="mr-1.5 h-3.5 w-3.5" /> Back to Common Issues
                </Button>
              )}
              <Button variant="outline" size="sm" onClick={newSession} disabled={streaming} className="h-8 text-xs font-medium">
                <Plus className="mr-1.5 h-3.5 w-3.5" /> New Chat
              </Button>
              {sessionId && (
                <div className="flex gap-1 border-l pl-2">
                  <Button variant="ghost" size="icon" onClick={clearChat} title="Clear conversation" className="h-8 w-8">
                    <Plus className="h-4 w-4 rotate-45" />
                  </Button>
                  <Button variant="ghost" size="icon" onClick={deleteCurrentSession} title="Delete conversation" className="h-8 w-8 text-destructive">
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              )}
            </div>
          </div>

          {/* Content Area */}
          <div ref={scrollRef} className="flex-1 space-y-4 overflow-y-auto p-4 sm:p-6">
          {/* STEP 1: INITIAL CLEAN COMMON ISSUES VIEW */}
          {!selectedIssue && messages.length === 0 && (
            <div className="mx-auto max-w-xl space-y-5 py-4">
              <div className="text-center space-y-1.5">
                <div className="mx-auto flex h-11 w-11 items-center justify-center rounded-xl bg-primary/10 text-primary mb-1 shadow-inner">
                  <Bot className="h-6 w-6" />
                </div>
                <h2 className="text-xl font-bold tracking-tight text-foreground">
                  Hi! How can I help you?
                </h2>
                <p className="text-xs text-muted-foreground">
                  Select a common issue below or describe your problem in the input box.
                </p>
              </div>

              {/* COMMON ISSUES - COMPACT HORIZONTAL ROW PILLS */}
              <div className="space-y-3 pt-2 text-center">
                <h3 className="text-[11px] font-bold uppercase tracking-wider text-muted-foreground border-b border-border/40 pb-2">
                  COMMON ISSUES
                </h3>

                <div className="flex flex-wrap justify-center gap-2">
                  {COMMON_ISSUES_DATA.map((issue) => (
                    <button
                      key={issue.id}
                      onClick={() => handleIssueClick(issue)}
                      className="inline-flex items-center text-xs font-medium px-3.5 py-1.5 rounded-full border border-border/80 bg-card hover:border-primary hover:bg-primary/10 hover:text-primary transition-all duration-150 text-foreground cursor-pointer shadow-sm focus:outline-none focus:ring-2 focus:ring-primary/20"
                    >
                      {issue.title}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* STEP 2 & 3: SELECTED ISSUE AI DIAGNOSIS & SOLUTION VIEW */}
          {selectedIssue && (
            <div className="mx-auto max-w-3xl space-y-5">
              {/* Back Button */}
              <div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={resetToCommonIssues}
                  className="text-xs text-muted-foreground hover:text-foreground pl-0 hover:bg-transparent"
                >
                  <ArrowLeft className="mr-1.5 h-3.5 w-3.5" /> Back to Common Issues
                </Button>
              </div>

              {/* Greeting */}
              <div className="rounded-xl bg-card border border-border/70 p-4 space-y-1">
                <p className="text-sm font-semibold text-foreground flex items-center gap-1.5">
                  👋 Hi! I understand you're having a {selectedIssue.title} problem.
                </p>
                <p className="text-xs text-muted-foreground">Let me analyze the issue for you.</p>
              </div>

              {/* AI ANALYSIS CARD */}
              <div className="rounded-xl border border-border/80 bg-card p-5 space-y-4 shadow-sm">
                <div className="border-b pb-3 flex items-center justify-between">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-primary flex items-center gap-2">
                    <Sparkles className="h-4 w-4 text-amber-500" /> AI ANALYSIS
                  </h3>
                  <span
                    className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold border ${
                      selectedIssue.priority === "Critical"
                        ? "bg-rose-500/10 text-rose-500 border-rose-500/30"
                        : selectedIssue.priority === "High"
                        ? "bg-orange-500/10 text-orange-500 border-orange-500/30"
                        : selectedIssue.priority === "Medium"
                        ? "bg-amber-500/10 text-amber-500 border-amber-500/30"
                        : "bg-blue-500/10 text-blue-500 border-blue-500/30"
                    }`}
                  >
                    {selectedIssue.priority} Priority
                  </span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                  <div className="rounded-lg bg-muted/50 p-3 border border-border/40 space-y-1">
                    <span className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground block">
                      Issue Type
                    </span>
                    <span className="font-semibold text-foreground text-sm">{selectedIssue.issueType}</span>
                  </div>

                  <div className="rounded-lg bg-muted/50 p-3 border border-border/40 space-y-1">
                    <span className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground block">
                      AI Confidence
                    </span>
                    <span className="font-semibold text-foreground text-sm">{selectedIssue.confidence}%</span>
                  </div>

                  <div className="rounded-lg bg-muted/50 p-3 border border-border/40 sm:col-span-2 space-y-1">
                    <span className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground block">
                      Root Cause
                    </span>
                    <span className="font-medium text-foreground">{selectedIssue.rootCause}</span>
                  </div>

                  <div className="rounded-lg bg-muted/50 p-3 border border-border/40 sm:col-span-2 space-y-1.5">
                    <span className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground block">
                      Possible Causes
                    </span>
                    <ul className="space-y-1 text-xs text-foreground/90 font-medium pl-1">
                      {selectedIssue.possibleCauses.map((cause, i) => (
                        <li key={i} className="flex items-center gap-1.5">
                          <span className="text-primary font-bold">•</span>
                          <span>{cause}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>

              {/* RECOMMENDED SOLUTION CARD */}
              <div className="rounded-xl border border-border/80 bg-card p-5 space-y-3 shadow-sm">
                <h3 className="text-xs font-bold uppercase tracking-wider text-primary border-b pb-3">
                  RECOMMENDED SOLUTION
                </h3>
                <ol className="list-decimal list-inside space-y-2 text-xs text-foreground/90 font-medium leading-relaxed">
                  {selectedIssue.solutionSteps.map((step, i) => (
                    <li key={i} className="marker:text-primary marker:font-bold py-0.5">
                      {step}
                    </li>
                  ))}
                </ol>
              </div>

              {/* SIMILAR TICKETS */}
              {!loadingSimilar && similarTickets.length > 0 && issueState === "diagnosing" && (
                <SimilarTicketsInline
                  tickets={similarTickets}
                  onRaiseTicket={handleRaiseTicketClick}
                />
              )}

              {/* STEP 4: YES / NO FLOW */}
              {issueState === "diagnosing" && (
                <div className="rounded-xl border border-primary/20 bg-card p-4 space-y-3 text-center sm:text-left flex flex-col sm:flex-row items-center justify-between gap-3 shadow-sm">
                  <span className="text-sm font-semibold text-foreground">Did this solve your problem?</span>
                  <div className="flex items-center gap-2.5 w-full sm:w-auto">
                    <Button
                      size="sm"
                      onClick={handleSolveClick}
                      className="flex-1 sm:flex-initial bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-xs h-9 px-4"
                    >
                      <CheckCircle2 className="mr-1.5 h-4 w-4" /> ✓ Yes, Problem Solved
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={handleRaiseTicketClick}
                      className="flex-1 sm:flex-initial border-rose-500/40 text-rose-600 hover:bg-rose-500/10 dark:text-rose-400 font-semibold text-xs h-9 px-4"
                    >
                      <XCircle className="mr-1.5 h-4 w-4 text-rose-500" /> ✕ No, Raise Ticket
                    </Button>
                  </div>
                </div>
              )}

              {/* YES RESPONSE VIEW */}
              {issueState === "solved" && (
                <div className="rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-5 space-y-3 text-center sm:text-left">
                  <div className="flex items-center gap-2 text-emerald-600 dark:text-emerald-400 font-bold text-base">
                    <CheckCircle2 className="h-5 w-5" /> ✓ Problem Resolved
                  </div>
                  <p className="text-xs text-foreground/90 font-medium">Glad I could help! No ticket is required.</p>
                  <div>
                    <Button size="sm" variant="outline" onClick={resetToCommonIssues} className="text-xs h-8">
                      <ArrowLeft className="mr-1.5 h-3.5 w-3.5" /> Back to Common Issues
                    </Button>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* CHAT MESSAGES IF ANY LIVE LLM CONVERSATION */}
          {!selectedIssue && messages.length > 0 && (
            <div className="space-y-4">
              {messages.map((m, i) => (
                <MessageBubble key={m.id} message={m} streaming={streaming && i === messages.length - 1} />
              ))}
            </div>
          )}

          {/* STREAMING INDICATOR */}
          {streaming && !selectedIssue && (
            <div className="flex items-start gap-3">
              <Avatar className="h-8 w-8 border border-primary/20">
                <AvatarFallback className="bg-primary text-primary-foreground">
                  <Bot className="h-4 w-4" />
                </AvatarFallback>
              </Avatar>
              <div className="rounded-xl bg-muted px-4 py-3 border border-border/50 shadow-sm">
                <span className="flex items-center gap-1.5 text-muted-foreground text-xs font-medium">
                  <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-primary" />
                  <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-primary [animation-delay:120ms]" />
                  <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-primary [animation-delay:240ms]" />
                  <span>AI is analyzing issue and generating response...</span>
                </span>
              </div>
            </div>
          )}

          {/* AI ANALYSIS / RECOMMENDATION CARD FOR UNMATCHED QUERIES */}
          {!selectedIssue && analysis && (
            <RecommendationCard
              analysis={analysis}
              draft={draft}
              confirmBusy={streaming}
              onConfirm={draft ? () => confirmDraft(draft.id) : undefined}
              onDismiss={draft ? () => dismissDraft(draft.id) : undefined}
            />
          )}
          {!selectedIssue && draft && !analysis && (
            <RecommendationCard
              analysis={null}
              draft={draft}
              confirmBusy={streaming}
              onConfirm={() => confirmDraft(draft.id)}
              onDismiss={() => dismissDraft(draft.id)}
            />
          )}
        </div>

        {/* STEP 7: TEXT INPUT BAR AT BOTTOM */}
        <div className="border-t bg-card p-3">
          {!selectedIssue && drafts.length > 0 && (
            <div className="mb-2.5 flex flex-wrap items-center gap-2">
              <span className="text-xs font-medium text-muted-foreground flex items-center gap-1">
                <Sparkles className="h-3 w-3 text-amber-500" /> Pending Ticket Recommendations:
              </span>
              {drafts.map((d) => (
                <span
                  key={d.id}
                  className="rounded-full border border-amber-500/30 bg-amber-500/10 px-3 py-1 text-xs font-medium text-foreground"
                >
                  {d.title} ·{" "}
                  <button className="text-primary font-semibold hover:underline" onClick={() => confirmDraft(d.id)}>
                    Confirm & Create
                  </button>{" "}
                  ·{" "}
                  <button className="text-muted-foreground hover:underline" onClick={() => dismissDraft(d.id)}>
                    Dismiss
                  </button>
                </span>
              ))}
            </div>
          )}
          <div className="flex items-end gap-2">
            <Textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  send();
                }
              }}
              placeholder="Type your IT issue here..."
              rows={2}
              className="resize-none bg-background border-border/80 focus:border-primary"
              disabled={streaming}
            />
            <Button size="icon" onClick={send} disabled={streaming || !input.trim()} className="h-10 w-10 shrink-0">
              <Send className="h-4 w-4" />
            </Button>
          </div>
        </div>
        </div>
      </Card>
    </div>
  );
}

function MessageBubble({ message, streaming }: { message: ChatMessage; streaming?: boolean }) {
  const isUser = message.role === "user";
  const [copied, setCopied] = useState(false);

  const copyToClipboard = () => {
    navigator.clipboard.writeText(message.content).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  return (
    <div className={`flex gap-3 ${isUser ? "justify-end" : "justify-start"}`}>
      {!isUser && (
        <Avatar className="h-8 w-8 border border-primary/20 shrink-0">
          <AvatarFallback className="bg-primary text-primary-foreground">
            <Bot className="h-4 w-4" />
          </AvatarFallback>
        </Avatar>
      )}
      <div
        className={`group relative max-w-[85%] rounded-2xl px-4 py-3 ${
          isUser
            ? "bg-primary text-primary-foreground shadow-sm rounded-tr-none"
            : "bg-muted text-foreground border border-border/50 rounded-tl-none"
        }`}
      >
        {isUser ? (
          <p className="whitespace-pre-wrap text-sm leading-relaxed">{message.content}</p>
        ) : message.content ? (
          <div className="text-sm prose prose-sm dark:prose-invert max-w-none leading-relaxed">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.content}</ReactMarkdown>
          </div>
        ) : (
          <span className="flex items-center gap-1.5 text-muted-foreground py-1">
            <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-current" />
            <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-current [animation-delay:120ms]" />
            <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-current [animation-delay:240ms]" />
          </span>
        )}
        {!isUser && message.content && (
          <button
            onClick={copyToClipboard}
            className="absolute top-2 right-2 rounded p-1 opacity-0 transition-opacity hover:bg-accent group-hover:opacity-100"
            title="Copy response"
          >
            {copied ? (
              <CheckCircle2 className="h-3.5 w-3.5 text-green-500" />
            ) : (
              <Copy className="h-3.5 w-3.5 text-muted-foreground" />
            )}
          </button>
        )}
        <p className="mt-1 text-[10px] opacity-60 text-right">
          {streaming && !message.content ? "…" : formatRelative(message.created_at)}
        </p>
      </div>
    </div>
  );
}

function RecommendationCard({
  analysis,
  draft,
  onConfirm,
  onDismiss,
  confirmBusy,
}: {
  analysis: Analysis | null;
  draft: DraftEvent | null;
  onConfirm?: () => void;
  onDismiss?: () => void;
  confirmBusy?: boolean;
}) {
  const meta = analysis ?? {
    intent: draft?.intent ?? "ticket_creation",
    category: draft?.category ?? "General",
    priority: draft?.priority ?? "medium",
    department: draft?.department ?? null,
    confidence: draft?.confidence ?? 0,
    summary: draft?.description ?? "",
    should_create_ticket: true,
    sentiment: null,
  };

  const priorityColors: Record<string, string> = {
    low: "text-blue-600 dark:text-blue-400 bg-blue-500/10 border-blue-500/30",
    medium: "text-amber-600 dark:text-amber-400 bg-amber-500/10 border-amber-500/30",
    high: "text-orange-600 dark:text-orange-400 bg-orange-500/10 border-orange-500/30",
    critical: "text-rose-600 dark:text-rose-400 bg-rose-500/10 border-rose-500/30",
  };

  const priorityBadge = priorityColors[meta.priority?.toLowerCase() || "medium"] || priorityColors.medium;

  return (
    <div className="rounded-2xl border border-amber-500/30 bg-amber-500/10 p-4 text-foreground shadow-sm transition-all dark:bg-amber-950/40 dark:border-amber-500/30">
      <div className="mb-3 flex items-center justify-between border-b border-amber-500/20 pb-2.5">
        <div className="flex items-center gap-2">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-amber-500/20 text-amber-600 dark:text-amber-400">
            <Sparkles className="h-4 w-4" />
          </div>
          <div>
            <h4 className="text-sm font-semibold text-foreground">AI Ticket Recommendation</h4>
            <p className="text-[11px] text-muted-foreground">The AI proposed a ticket draft based on your issue</p>
          </div>
        </div>
        <span className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold ${priorityBadge}`}>
          {titleCase(meta.priority)} Priority
        </span>
      </div>

      <div className="grid grid-cols-2 gap-2 text-xs sm:grid-cols-4">
        <div className="rounded-lg bg-background/80 p-2.5 border border-border/50">
          <span className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground block mb-0.5">Intent</span>
          <span className="font-semibold text-foreground">{titleCase(meta.intent)}</span>
        </div>
        <div className="rounded-lg bg-background/80 p-2.5 border border-border/50">
          <span className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground block mb-0.5">Category</span>
          <span className="font-semibold text-foreground">{meta.category || "General"}</span>
        </div>
        <div className="rounded-lg bg-background/80 p-2.5 border border-border/50">
          <span className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground block mb-0.5">Department</span>
          <span className="font-semibold text-foreground">{meta.department || "IT Support"}</span>
        </div>
        <div className="rounded-lg bg-background/80 p-2.5 border border-border/50">
          <span className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground block mb-0.5">Confidence</span>
          <span className="font-semibold text-foreground">{Math.round(Number(meta.confidence) * 100)}%</span>
        </div>
        {meta.sentiment && (
          <div className="rounded-lg bg-background/80 p-2.5 border border-border/50">
            <span className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground block mb-0.5">Sentiment</span>
            <span className="font-semibold text-foreground">{titleCase(meta.sentiment)}</span>
          </div>
        )}
      </div>

      {meta.summary && (
        <div className="mt-2.5 rounded-lg bg-background/80 p-2.5 border border-border/50 text-xs">
          <span className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground block mb-0.5">Summary</span>
          <p className="text-foreground/90 leading-relaxed">{meta.summary}</p>
        </div>
      )}

      {(onConfirm || onDismiss) && (
        <div className="mt-3.5 flex items-center gap-2">
          {onConfirm && (
            <Button
              size="sm"
              onClick={onConfirm}
              disabled={confirmBusy}
              className="bg-amber-600 text-white hover:bg-amber-700 dark:bg-amber-600 dark:hover:bg-amber-500 font-medium"
            >
              <CheckCircle2 className="mr-1.5 h-3.5 w-3.5" /> Confirm & Create Ticket
            </Button>
          )}
          {onDismiss && (
            <Button
              size="sm"
              variant="outline"
              onClick={onDismiss}
              disabled={confirmBusy}
              className="text-muted-foreground hover:text-foreground"
            >
              Dismiss
            </Button>
          )}
        </div>
      )}
    </div>
  );
}