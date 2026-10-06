import { useState, useEffect, useRef } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  Sparkles,
  Paperclip,
  ArrowLeft,
  CheckCircle2,
  AlertCircle,
  FileText,
  X,
  Bot,
} from "lucide-react";
import { ticketApi, chatApi } from "@/api/endpoints";
import { extractErrorMessage } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
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
import SimilarTickets from "@/components/tickets/similar-tickets";
import type { SimilarTicket } from "@/models/types";

const CATEGORY_OPTIONS = [
  "Network",
  "Hardware",
  "Software",
  "Account & Access",
  "Email",
  "Server",
  "Other",
];

const CATEGORY_MAP: Record<string, string> = {
  Network: "Network & VPN",
  Hardware: "Hardware",
  Software: "Software",
  "Account & Access": "Identity & Access",
  Email: "Email",
  Server: "IT Operations",
  Other: "General",
};

// Actual department values already used by this project (AI assistant diagnoses + backend AI rules).
const DEPARTMENT_OPTIONS = [
  "IT Support",
  "Network Support",
  "Email Support",
  "Hardware Support",
  "Infrastructure Team",
  "Software Services",
  "IT Operations",
  "Security",
];

const PRIORITY_OPTIONS = [
  { value: "low", label: "Low" },
  { value: "medium", label: "Medium" },
  { value: "high", label: "High" },
  { value: "critical", label: "Critical" },
];

const PRIORITY_VALUES = PRIORITY_OPTIONS.map((p) => p.value);

export default function CreateTicketPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const queryClient = useQueryClient();

  const [loading, setLoading] = useState(false);
  const [aiAnalyzing, setAiAnalyzing] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const [errors, setErrors] = useState<{ title?: string; description?: string }>({});
  const [similarTickets, setSimilarTickets] = useState<SimilarTicket[]>([]);

  const [form, setForm] = useState({
    title: "",
    description: "",
    category: "Network",
    priority: "medium",
    department: "",
  });

  const prefillAppliedRef = useRef(false);

  // Radix 2.3.x's hidden native <select> fires onValueChange("") whenever a
  // controlled value has no mounted option (i.e. while the dropdown is closed).
  // No option here has an empty value, so dropping "" stops the AI prefill from
  // being wiped out. Functional update avoids stale-closure resets of the other
  // fields.
  const updateField = (field: keyof typeof form) => (value: string) => {
    if (value !== "") setForm((prev) => ({ ...prev, [field]: value }));
  };

  useEffect(() => {
    // Prefer router state (set by the AI Assistant); fall back to the persisted
    // copy so the three dropdown values can never be lost in transit.
    let prefill = location.state?.prefill;
    if (!prefill) {
      try {
        const raw = sessionStorage.getItem("itdesk.ticketPrefill");
        if (raw) prefill = JSON.parse(raw);
      } catch {
        prefill = null;
      }
    }
    console.debug("[CreateTicket] mount/update location.state prefill:", prefill, "key:", location.key);
    if (prefill && !prefillAppliedRef.current) {
      prefillAppliedRef.current = true;
      try {
        sessionStorage.removeItem("itdesk.ticketPrefill");
      } catch {
        /* ignore */
      }
      const mappedCategory = mapToDropdownCategory(prefill.category, prefill.issueType);
      const mappedPriority = (prefill.priority || "medium").toLowerCase();
      const mappedDepartment = mapToDropdownDepartment(prefill.department, prefill.issueType || prefill.category);
      console.debug("[CreateTicket] mapped values:", { mappedCategory, mappedPriority, mappedDepartment });
      setForm({
        title: prefill.title || "",
        description: prefill.description || "",
        category: mappedCategory,
        priority: mappedPriority,
        department: mappedDepartment,
      });
      toast.info("Ticket details pre-filled from AI diagnosis.");
    }
  }, [location.key]);

  useEffect(() => {
    const timer = setTimeout(async () => {
      if (form.title.trim().length >= 3 || form.description.trim().length >= 3) {
        try {
          const res = await ticketApi.findSimilar({
            title: form.title,
            description: form.description,
            category: form.category,
            priority: form.priority,
            threshold: 70,
            limit: 5,
          });
          setSimilarTickets(res.similar_tickets);
        } catch {
          setSimilarTickets([]);
        }
      } else {
        setSimilarTickets([]);
      }
    }, 500);
    return () => clearTimeout(timer);
  }, [form.title, form.description, form.category, form.priority]);

  // Map the AI's category/issueType onto one of the EXACT dropdown values in
  // CATEGORY_OPTIONS (used as the <SelectItem value>).
  function mapToDropdownCategory(cat?: string, issueType?: string): string {
    if (!cat && !issueType) return "Network";
    const catLower = (cat || "").trim().toLowerCase();
    const typeLower = (issueType || "").trim().toLowerCase();
    const exact = CATEGORY_OPTIONS.find(
      (c) => c.toLowerCase() === catLower || c.toLowerCase() === typeLower,
    );
    if (exact) return exact;

    const source = `${catLower} ${typeLower}`;
    if (source.includes("server") || source.includes("infrastructure") || source.includes("database") || source.includes("host down"))
      return "Server";
    if (source.includes("mail") || source.includes("outlook"))
      return "Email";
    if (source.includes("hard") || source.includes("printer") || source.includes("laptop") || source.includes("peripheral") || source.includes("monitor"))
      return "Hardware";
    if (source.includes("soft") || source.includes("application") || source.includes("install"))
      return "Software";
    if (source.includes("login") || source.includes("password") || source.includes("account") || source.includes("authentication") || source.includes("ident") || source.includes("access"))
      return "Account & Access";
    if (source.includes("net") || source.includes("vpn") || source.includes("wifi") || source.includes("internet") || source.includes("lan") || source.includes("dns"))
      return "Network";
    if (source.includes("performance") || source.includes("slow") || source.includes("crash") || source.includes("freeze"))
      return "Hardware";
    if (source.includes("oper")) return "Server";
    return "Other";
  }

  // Derive a department from the AI's issueType/category when the AI didn't
  // provide one. Returns only values present in DEPARTMENT_OPTIONS.
  function mapToDepartment(issueType?: string, category?: string): string {
    const source = (issueType || category || "").toLowerCase();
    if (source.includes("server") || source.includes("infrastructure") || source.includes("database") || source.includes("host"))
      return "Infrastructure Team";
    if (source.includes("vpn") || source.includes("network") || source.includes("wi-fi") || source.includes("internet"))
      return "Network Support";
    if (source.includes("printer") || source.includes("hardware") || source.includes("laptop") || source.includes("keyboard") || source.includes("monitor"))
      return "Hardware Support";
    if (source.includes("software") || source.includes("application") || source.includes("system error"))
      return "Software Services";
    if (source.includes("email") || source.includes("mailbox") || source.includes("outlook"))
      return "Email Support";
    if (source.includes("login") || source.includes("password") || source.includes("account") || source.includes("authentication") || source.includes("access"))
      return "IT Support";
    if (source.includes("security") || source.includes("suspicious"))
      return "Security";
    return "IT Support";
  }

  // Resolve the department to a value that actually exists in DEPARTMENT_OPTIONS
  // so the <Select value={form.department}> always matches a SelectItem.
  function mapToDropdownDepartment(dept?: string | null, source?: string): string {
    if (dept) {
      const d = dept.trim();
      const exact = DEPARTMENT_OPTIONS.find((o) => o.toLowerCase() === d.toLowerCase());
      if (exact) return exact;
      // The AI assistant labels the login team "IT Support Team" — collapse to "IT Support".
      if (/^it support team$/i.test(d)) return "IT Support";
    }
    const derived = mapToDepartment(source);
    return DEPARTMENT_OPTIONS.includes(derived) ? derived : "IT Support";
  }

  const validate = () => {
    const newErrors: { title?: string; description?: string } = {};
    if (!form.title.trim()) {
      newErrors.title = "Ticket Title is required.";
    } else if (form.title.trim().length < 3) {
      newErrors.title = "Title must be at least 3 characters.";
    }

    if (!form.description.trim()) {
      newErrors.description = "Description is required.";
    } else if (form.description.trim().length < 3) {
      newErrors.description = "Description must be at least 3 characters.";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleAnalyzeWithAI = async () => {
    if (!form.title.trim() && !form.description.trim()) {
      toast.error("Please enter a Title or Description before analyzing with AI.");
      return;
    }
    setAiAnalyzing(true);
    try {
      const prompt = `Analyze this IT support issue:\nTitle: ${form.title}\nDescription: ${form.description}`;
      let aiText = "";
      const s = await chatApi.createSession();
      if (!s?.id) {
        throw new Error("Could not start an AI session. Please sign in and try again.");
      }
      await chatApi.sendStream(
        s.id,
        prompt,
        (token) => {
          aiText += token;
        },
        () => {},
      );

      const lower = (form.title + " " + form.description + " " + aiText).toLowerCase();
      let suggestedCategory = form.category;
      if (lower.includes("vpn") || lower.includes("wifi") || lower.includes("internet") || lower.includes("net")) {
        suggestedCategory = "Network";
      } else if (lower.includes("server") || lower.includes("host") || lower.includes("db down")) {
        suggestedCategory = "Server";
      } else if (lower.includes("login") || lower.includes("password") || lower.includes("access") || lower.includes("lock")) {
        suggestedCategory = "Account & Access";
      } else if (lower.includes("email") || lower.includes("outlook") || lower.includes("mail")) {
        suggestedCategory = "Email";
      } else if (lower.includes("printer") || lower.includes("screen") || lower.includes("laptop")) {
        suggestedCategory = "Hardware";
      }

      let suggestedPriority = form.priority;
      if (lower.includes("critical") || lower.includes("outage") || lower.includes("down")) {
        suggestedPriority = "critical";
      } else if (lower.includes("high") || lower.includes("cannot work") || lower.includes("urgent")) {
        suggestedPriority = "high";
      }

      setForm((prev) => ({
        ...prev,
        category: suggestedCategory,
        priority: suggestedPriority,
        description:
          prev.description +
          (aiText ? `\n\n--- NexDesk AI Analysis ---\n${aiText.trim()}` : ""),
      }));

      toast.success("AI Analysis complete! Category and Priority updated.");
    } catch (e: any) {
      toast.error(e?.message ?? "AI analysis failed.");
    } finally {
      setAiAnalyzing(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    console.debug("[CreateTicket] handleSubmit form:", form);
    if (!validate()) {
      toast.error("Please fill in all required fields.");
      return;
    }

    setLoading(true);
    try {
      const backendCategory = (CATEGORY_MAP[form.category] || "General").slice(0, 80);
      const priority = PRIORITY_VALUES.includes(form.priority) ? form.priority : "medium";
      const department = (form.department || "").trim().slice(0, 120) || undefined;
      const payload = {
        title: form.title.trim().slice(0, 255),
        description: form.description.trim(),
        category: backendCategory,
        priority,
        department,
      };
      console.debug("[CreateTicket] API payload:", payload);
      const created = await ticketApi.create(payload);

      if (!created) {
        throw new Error("Ticket creation returned an empty response.");
      }
      console.debug("[CreateTicket] API response:", created);

      if (file && created.id) {
        try {
          await ticketApi.upload(created.id, file);
        } catch {
          toast.warning("Ticket created, but attachment upload failed.");
        }
      }

      toast.success(`Ticket ${created.ticket_no ?? `#${created.id}`} submitted successfully!`);

      queryClient.invalidateQueries({ queryKey: ["tickets"] });
      queryClient.invalidateQueries({ queryKey: ["my-tickets"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard", "stats"] });
      queryClient.invalidateQueries({ queryKey: ["analytics"] });

      try {
        await navigate("/my-tickets");
      } catch (navErr) {
        console.error("Navigation error after ticket creation:", navErr);
        toast.error("Ticket created, but navigation failed. Please go to My Tickets manually.");
      }
    } catch (err: unknown) {
      console.error("Ticket creation error:", err);
      toast.error(extractErrorMessage(err, "Failed to create ticket."));
    } finally {
      setLoading(false);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setFile(e.dataTransfer.files[0]);
    }
  };

  return (
    <div className="w-full max-w-6xl mx-auto py-8 px-4 sm:px-6 lg:px-8 space-y-8 animate-fade-in">
      {/* 1. PAGE HEADER */}
      <div className="relative">
        <div className="absolute -top-6 -left-6 w-32 h-32 bg-blue-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute -top-6 -right-6 w-32 h-32 bg-purple-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 relative">
          <div>
            <div className="flex items-center gap-3">
              <Button
                variant="ghost"
                size="icon"
                onClick={() => navigate(-1)}
                className="h-9 w-9 text-muted-foreground hover:text-foreground hover:bg-surface-hover transition-colors"
                title="Go back"
              >
                <ArrowLeft className="h-4 w-4" />
              </Button>
              <div>
                <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-foreground flex items-center gap-3">
                  <span className="relative inline-flex">
                    <span className="absolute -inset-1 bg-gradient-to-r from-blue-500 to-indigo-600 rounded-lg blur opacity-20" />
                    <span className="relative bg-gradient-to-br from-blue-500 to-indigo-600 text-white p-1.5 rounded-lg">
                      <FileText className="h-5 w-5 sm:h-6 sm:w-6" />
                    </span>
                  </span>
                  Create New Ticket
                </h1>
                <p className="text-sm text-muted-foreground mt-1.5 ml-12">
                  Submit an IT issue and let NexDesk help analyze it.
                </p>
              </div>
            </div>
          </div>

          <Button
            variant="outline"
            size="sm"
            onClick={() => navigate("/ai-assistant")}
            className="self-start sm:self-auto border-purple-500/30 bg-purple-500/5 hover:bg-purple-500/15 text-purple-300 hover:text-purple-200 text-xs font-semibold gap-2 transition-all shadow-sm shadow-purple-500/5"
          >
            <Bot className="h-3.5 w-3.5" />
            Launch AI Assistant
          </Button>
        </div>
      </div>

      {/* 2. ISSUE DETAILS CARD */}
      <form onSubmit={handleSubmit} className="space-y-6">
        <Card className="border border-border/60 bg-card/80 backdrop-blur-xl shadow-2xl overflow-visible relative">
          <div className="absolute inset-0 bg-gradient-to-br from-blue-500/5 via-transparent to-purple-500/5 pointer-events-none" />
          <CardHeader className="border-b border-border/50 bg-surface/40 px-6 sm:px-8 py-5 relative">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-500/10 border border-blue-500/20">
                <FileText className="h-5 w-5 text-blue-400" />
              </div>
              <div>
                <CardTitle className="text-base font-bold text-foreground">
                  Issue Details
                </CardTitle>
                <CardDescription className="text-xs text-muted-foreground mt-0.5">
                  Provide necessary details so the IT team can quickly resolve your request.
                </CardDescription>
              </div>
            </div>
          </CardHeader>

          <CardContent className="p-6 sm:p-8 relative">
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
              {/* LEFT COLUMN: Title & Description */}
              <div className="lg:col-span-7 space-y-6">
                {/* Field 1: Ticket Title */}
                <div className="space-y-2.5">
                  <Label htmlFor="title" className="text-sm font-semibold text-foreground flex items-center gap-1.5">
                    Ticket Title
                    <span className="text-rose-500 text-xs">*</span>
                  </Label>
                  <Input
                    id="title"
                    value={form.title}
                    onChange={(e) => {
                      setForm({ ...form, title: e.target.value });
                      if (errors.title) setErrors({ ...errors, title: undefined });
                    }}
                    placeholder="Enter a short description of your issue"
                    className={`h-12 bg-surface border-border/80 focus:border-blue-500 text-foreground placeholder:text-muted-foreground/60 rounded-xl transition-all ${
                      errors.title ? "border-rose-500/70 bg-rose-500/5 shadow-sm shadow-rose-500/10" : "hover:border-border-strong"
                    }`}
                  />
                  {errors.title && (
                    <div className="flex items-center gap-1.5 text-xs text-rose-400 bg-rose-500/10 px-3 py-2 rounded-lg border border-rose-500/20">
                      <AlertCircle className="h-3.5 w-3.5 shrink-0" />
                      <span className="font-medium">{errors.title}</span>
                    </div>
                  )}
                </div>

                {/* Field 2: Description */}
                <div className="space-y-2.5">
                  <Label htmlFor="description" className="text-sm font-semibold text-foreground flex items-center gap-1.5">
                    Description
                    <span className="text-rose-500 text-xs">*</span>
                  </Label>
                  <Textarea
                    id="description"
                    value={form.description}
                    onChange={(e) => {
                      setForm({ ...form, description: e.target.value });
                      if (errors.description) setErrors({ ...errors, description: undefined });
                    }}
                    placeholder="Describe your problem in detail..."
                    rows={8}
                    className={`bg-surface border-border/80 focus:border-blue-500 text-foreground placeholder:text-muted-foreground/60 resize-y rounded-xl transition-all ${
                      errors.description ? "border-rose-500/70 bg-rose-500/5 shadow-sm shadow-rose-500/10" : "hover:border-border-strong"
                    }`}
                  />
                  {errors.description && (
                    <div className="flex items-center gap-1.5 text-xs text-rose-400 bg-rose-500/10 px-3 py-2 rounded-lg border border-rose-500/20">
                      <AlertCircle className="h-3.5 w-3.5 shrink-0" />
                      <span className="font-medium">{errors.description}</span>
                    </div>
                  )}
                </div>
              </div>

              {/* RIGHT COLUMN: Category, Priority, Attachment */}
              <div className="lg:col-span-5 space-y-6">
                {/* Field 3: Category */}
                <div className="space-y-2.5">
                  <Label className="text-sm font-semibold text-foreground">Category</Label>
                  <Select value={form.category} onValueChange={updateField("category")}>
                    <SelectTrigger className="h-12 bg-surface border-border/80 focus:border-blue-500 text-foreground rounded-xl hover:border-border-strong transition-all">
                      <SelectValue placeholder="Select Category">
                        {CATEGORY_OPTIONS.find((c) => c === form.category) ?? "Select Category"}
                      </SelectValue>
                    </SelectTrigger>
                    <SelectContent align="start" side="bottom" sideOffset={8} avoidCollisions={false} className="bg-card border-border/80 rounded-xl shadow-2xl max-h-[170px] overflow-y-auto">
                      {CATEGORY_OPTIONS.map((cat) => (
                        <SelectItem key={cat} value={cat} className="rounded-lg">
                          {cat}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {/* Field 4: Priority */}
                <div className="space-y-2.5">
                  <Label className="text-sm font-semibold text-foreground">Priority</Label>
                  <Select value={form.priority} onValueChange={updateField("priority")}>
                    <SelectTrigger className="h-12 bg-surface border-border/80 focus:border-blue-500 text-foreground rounded-xl hover:border-border-strong transition-all">
                      <SelectValue placeholder="Select Priority">
                        {PRIORITY_OPTIONS.find((p) => p.value === form.priority)?.label ?? "Select Priority"}
                      </SelectValue>
                    </SelectTrigger>
                    <SelectContent align="start" side="bottom" sideOffset={8} avoidCollisions={false} className="bg-card border-border/80 rounded-xl shadow-2xl max-h-[170px] overflow-y-auto">
                      {PRIORITY_OPTIONS.map((p) => (
                        <SelectItem key={p.value} value={p.value} className="rounded-lg">
                          <span className="flex items-center gap-2.5">
                            <span
                              className={`h-2 w-2 rounded-full ${
                                p.value === "critical"
                                  ? "bg-rose-500 shadow-sm shadow-rose-500/50"
                                  : p.value === "high"
                                  ? "bg-orange-500 shadow-sm shadow-orange-500/50"
                                  : p.value === "medium"
                                  ? "bg-amber-500 shadow-sm shadow-amber-500/50"
                                  : "bg-blue-500 shadow-sm shadow-blue-500/50"
                              }`}
                            />
                            {p.label}
                          </span>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {/* Field 5: Department */}
                <div className="space-y-2.5">
                  <Label className="text-sm font-semibold text-foreground">Department</Label>
                  <Select value={form.department} onValueChange={updateField("department")}>
                    <SelectTrigger className="h-12 bg-surface border-border/80 focus:border-blue-500 text-foreground rounded-xl hover:border-border-strong transition-all">
                      <SelectValue placeholder="Select Department">
                        {DEPARTMENT_OPTIONS.find((d) => d === form.department) ?? "Select Department"}
                      </SelectValue>
                    </SelectTrigger>
                    <SelectContent align="start" side="bottom" sideOffset={8} avoidCollisions={false} className="bg-card border-border/80 rounded-xl shadow-2xl max-h-[170px] overflow-y-auto">
                      {DEPARTMENT_OPTIONS.map((dep) => (
                        <SelectItem key={dep} value={dep} className="rounded-lg">
                          {dep}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {/* Field 6: Attachment Upload Box */}
                <div className="space-y-2.5">
                  <Label className="text-sm font-semibold text-foreground">Attachment</Label>
                  <div
                    onDragOver={(e) => {
                      e.preventDefault();
                      setDragOver(true);
                    }}
                    onDragLeave={() => setDragOver(false)}
                    onDrop={handleDrop}
                    className={`relative flex flex-col items-center justify-center p-6 border-2 border-dashed rounded-xl transition-all text-center cursor-pointer group ${
                      dragOver
                        ? "border-blue-500 bg-blue-500/10 scale-[1.01]"
                        : "border-border/80 bg-surface/50 hover:border-blue-500/40 hover:bg-surface hover:scale-[1.01]"
                    }`}
                  >
                    <input
                      type="file"
                      id="file-upload"
                      onChange={handleFileChange}
                      className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                    />
                    {!file ? (
                      <div className="space-y-3 pointer-events-none">
                        <div className="mx-auto flex h-11 w-11 items-center justify-center rounded-xl bg-blue-500/10 border border-blue-500/20 group-hover:scale-110 transition-transform">
                          <Paperclip className="h-5 w-5 text-blue-400" />
                        </div>
                        <p className="text-sm font-semibold text-foreground">
                          📎 Upload Screenshot / File
                        </p>
                        <p className="text-xs text-muted-foreground">
                          PNG, JPG, PDF or other supported files
                        </p>
                      </div>
                    ) : (
                      <div className="flex items-center justify-between w-full bg-card p-3 rounded-xl border border-border/80 text-xs shadow-sm">
                        <div className="flex items-center gap-2.5 truncate">
                          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-500/10 shrink-0">
                            <Paperclip className="h-4 w-4 text-blue-400" />
                          </div>
                          <div className="min-w-0">
                            <span className="truncate font-medium text-foreground block">{file.name}</span>
                            <span className="text-[10px] text-muted-foreground">
                              {Math.round(file.size / 1024)} KB
                            </span>
                          </div>
                        </div>
                        <Button
                          type="button"
                          variant="ghost"
                          size="icon"
                          onClick={(e) => {
                            e.stopPropagation();
                            setFile(null);
                          }}
                          className="h-7 w-7 text-muted-foreground hover:text-destructive hover:bg-destructive/10 shrink-0 rounded-lg transition-colors"
                        >
                          <X className="h-3.5 w-3.5" />
                        </Button>
                      </div>
                    )}
                  </div>
                </div>

                {user && (
                  <div className="pt-4 border-t border-border/40">
                    <div className="flex items-center gap-2.5 p-3 rounded-xl bg-surface/60 border border-border/40">
                      <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-500/10 text-blue-400 text-xs font-bold">
                        {user.full_name?.charAt(0)?.toUpperCase() ?? "U"}
                      </div>
                      <div className="min-w-0">
                        <p className="text-xs font-semibold text-foreground truncate">
                          {user.full_name}
                        </p>
                        <p className="text-[11px] text-muted-foreground truncate">
                          {user.email}
                        </p>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* SIMILAR TICKETS */}
        {similarTickets.length > 0 && (
          <SimilarTickets
            tickets={similarTickets}
            onSolved={() => setSimilarTickets([])}
            currentTitle={form.title}
            currentDescription={form.description}
            currentCategory={form.category}
            currentPriority={form.priority}
            currentDepartment={form.department}
          />
        )}

        {/* 3. BUTTONS AT BOTTOM */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-2">
          <Button
            type="button"
            variant="outline"
            onClick={handleAnalyzeWithAI}
            disabled={aiAnalyzing}
            className="w-full sm:w-auto border-purple-500/30 bg-purple-500/5 hover:bg-purple-500/15 text-purple-300 hover:text-purple-200 font-semibold text-sm h-12 px-6 rounded-xl transition-all shadow-sm shadow-purple-500/5 hover:shadow-md hover:shadow-purple-500/10 group"
          >
            {aiAnalyzing ? (
              <Spinner />
            ) : (
              <>
                <span className="relative inline-flex">
                  <span className="absolute -inset-0.5 bg-gradient-to-r from-purple-500 to-indigo-600 rounded-md blur opacity-30 group-hover:opacity-50 transition-opacity" />
                  <span className="relative">
                    <Sparkles className="mr-2 h-4 w-4 text-purple-400" />
                  </span>
                </span>
                Analyze with AI
              </>
            )}
          </Button>

          <div className="flex items-center gap-3 w-full sm:w-auto">
            <Button
              type="button"
              variant="outline"
              onClick={() => navigate("/my-tickets")}
              className="flex-1 sm:flex-initial h-12 px-8 font-semibold text-sm text-muted-foreground hover:text-foreground border-border/80 hover:bg-surface hover:border-border-strong rounded-xl transition-all"
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={loading}
              className="flex-1 sm:flex-initial h-12 px-8 font-bold text-sm bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white shadow-lg shadow-blue-600/25 hover:shadow-xl hover:shadow-blue-600/30 transition-all rounded-xl"
            >
              {loading ? (
                <Spinner />
              ) : (
                <>
                  <CheckCircle2 className="mr-2 h-4 w-4" />
                  Create Ticket
                </>
              )}
            </Button>
          </div>
        </div>
      </form>
    </div>
  );
}
