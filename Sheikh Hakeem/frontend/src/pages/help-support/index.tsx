import { useState } from "react";
import { Link } from "react-router-dom";
import {
  HelpCircle,
  ChevronDown,
  ChevronUp,
  Bot,
  ClipboardList,
  PlusCircle,
  Mail,
  MessageSquare,
  ArrowLeft,
  BookOpen,
  Zap,
  Search,
  Ticket,
  AlertCircle,
  Clock,
  CheckCircle2,
  Loader2,
  Upload,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { cn } from "@/lib/utils";

interface FAQItem {
  question: string;
  answer: string;
}

const FAQS: FAQItem[] = [
  {
    question: "How do I raise a ticket?",
    answer:
      "Navigate to My Tickets and click the 'Create Ticket' button. Fill in the title, description, and any relevant details. The AI Assistant can help you draft a clear description of your issue.",
  },
  {
    question: "How do I check my ticket status?",
    answer:
      "Go to My Tickets to see all your tickets and their current status. Each ticket shows its status (Open, In Progress, Pending, or Resolved) along with priority and creation date.",
  },
  {
    question: "How does the AI Assistant work?",
    answer:
      "The AI Assistant analyzes your IT issue description and provides insights including issue type, root cause analysis, priority suggestion, category, department routing, possible causes, recommended solutions, and links to similar resolved tickets.",
  },
  {
    question: "How can I find similar tickets?",
    answer:
      "When you describe your issue to the AI Assistant, it automatically searches for similar resolved tickets and displays them alongside its analysis. You can also browse All Tickets (admin) or My Tickets to find related issues.",
  },
  {
    question: "What does Open mean?",
    answer:
      "An Open ticket is one that has been created but not yet assigned or started by a support agent. It is waiting to be picked up and addressed.",
  },
  {
    question: "What does In Progress mean?",
    answer:
      "An In Progress ticket is actively being worked on by a support agent. The issue has been acknowledged and troubleshooting or resolution steps are underway.",
  },
  {
    question: "What does Pending mean?",
    answer:
      "A Pending ticket is waiting for additional information, either from the reporter or from an external dependency. No active work is being done until the pending item is resolved.",
  },
  {
    question: "What does Resolved mean?",
    answer:
      "A Resolved ticket indicates the issue has been fixed or addressed. The reporter can verify the resolution. If the issue persists, the ticket can be reopened.",
  },
  {
    question: "How do I upload a screenshot or file?",
    answer:
      "When creating or updating a ticket, use the file attachment option to upload screenshots or documents. Images and common file formats are supported to help illustrate your issue.",
  },
];

function FAQAccordion({ item }: { item: FAQItem }) {
  const [open, setOpen] = useState(false);

  return (
    <div className="border-b border-border last:border-b-0">
      <button
        onClick={() => setOpen(!open)}
        className="flex w-full items-center justify-between gap-4 py-4 text-left text-sm font-medium text-text-primary hover:text-primary transition-colors"
      >
        <span>{item.question}</span>
        {open ? (
          <ChevronUp className="h-4 w-4 shrink-0 text-text-muted" />
        ) : (
          <ChevronDown className="h-4 w-4 shrink-0 text-text-muted" />
        )}
      </button>
      {open && (
        <div className="pb-4 text-sm text-text-secondary leading-relaxed">
          {item.answer}
        </div>
      )}
    </div>
  );
}

export default function HelpSupportPage() {
  return (
    <div className="space-y-6 animate-fade-in max-w-4xl">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button
          variant="ghost"
          size="icon"
          onClick={() => window.history.back()}
          className="shrink-0"
        >
          <ArrowLeft className="h-5 w-5" />
        </Button>
        <div>
          <h1 className="page-title flex items-center gap-2">
            <HelpCircle className="h-6 w-6 text-primary" />
            Help & Support
          </h1>
          <p className="page-subtitle">
            Find answers to common questions and get the help you need.
          </p>
        </div>
      </div>

      {/* FAQ Section */}
      <Card className="card-elevated">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BookOpen className="h-5 w-5 text-primary" />
            Frequently Asked Questions
          </CardTitle>
          <CardDescription>
            Click on a question to expand the answer.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="divide-y divide-border">
            {FAQS.map((faq) => (
              <FAQAccordion key={faq.question} item={faq} />
            ))}
          </div>
        </CardContent>
      </Card>

      {/* AI Assistant Help */}
      <Card className="card-elevated">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Bot className="h-5 w-5 text-primary" />
            AI Assistant Help
          </CardTitle>
          <CardDescription>
            The AI Assistant helps you diagnose and resolve IT issues faster.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm text-text-secondary">
            Describe your IT issue to the AI Assistant and it will analyze your
            problem to provide:
          </p>
          <div className="grid gap-3 sm:grid-cols-2">
            {[
              { icon: AlertCircle, label: "Issue Type", desc: "Identifies the category of your problem" },
              { icon: Search, label: "Root Cause", desc: "Analyzes what's causing the issue" },
              { icon: Zap, label: "Priority", desc: "Suggests the urgency level" },
              { icon: Ticket, label: "Possible Causes", desc: "Lists potential reasons for the issue" },
              { icon: CheckCircle2, label: "Recommended Solution", desc: "Provides step-by-step fixes" },
              { icon: ClipboardList, label: "Similar Tickets", desc: "Finds resolved tickets like yours" },
            ].map((item) => (
              <div
                key={item.label}
                className="flex items-start gap-3 rounded-lg border border-border p-3 bg-surface/50"
              >
                <item.icon className="h-4 w-4 mt-0.5 shrink-0 text-primary" />
                <div>
                  <p className="text-sm font-medium text-text-primary">{item.label}</p>
                  <p className="text-xs text-text-muted">{item.desc}</p>
                </div>
              </div>
            ))}
          </div>
          <Button asChild variant="outline" className="mt-2">
            <Link to="/ai-assistant">
              <Bot className="h-4 w-4 mr-2" />
              Open AI Assistant
            </Link>
          </Button>
        </CardContent>
      </Card>

      {/* Ticket Support */}
      <Card className="card-elevated">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Ticket className="h-5 w-5 text-primary" />
            Ticket Support
          </CardTitle>
          <CardDescription>
            Quick access to manage and create tickets.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-3 sm:grid-cols-3">
            <Button asChild variant="outline" className="justify-start h-auto py-4">
              <Link to="/my-tickets" className="flex flex-col items-start gap-1">
                <div className="flex items-center gap-2">
                  <ClipboardList className="h-4 w-4 text-primary" />
                  <span className="font-medium">My Tickets</span>
                </div>
                <span className="text-xs text-text-muted text-left">
                  View and manage your tickets
                </span>
              </Link>
            </Button>
            <Button asChild variant="outline" className="justify-start h-auto py-4">
              <Link to="/ai-assistant" className="flex flex-col items-start gap-1">
                <div className="flex items-center gap-2">
                  <Bot className="h-4 w-4 text-primary" />
                  <span className="font-medium">AI Assistant</span>
                </div>
                <span className="text-xs text-text-muted text-left">
                  Get AI-powered diagnosis
                </span>
              </Link>
            </Button>
            <Button asChild variant="outline" className="justify-start h-auto py-4">
              <Link to="/create-ticket" className="flex flex-col items-start gap-1">
                <div className="flex items-center gap-2">
                  <PlusCircle className="h-4 w-4 text-primary" />
                  <span className="font-medium">Create Ticket</span>
                </div>
                <span className="text-xs text-text-muted text-left">
                  Raise a new support ticket
                </span>
              </Link>
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Contact Support */}
      <Card className="card-elevated">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Mail className="h-5 w-5 text-primary" />
            Contact Support
          </CardTitle>
          <CardDescription>
            Need more help? Reach out through the ticket system.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-start gap-3 rounded-lg border border-border p-4 bg-surface/50">
            <MessageSquare className="h-5 w-5 mt-0.5 shrink-0 text-primary" />
            <div>
              <p className="text-sm font-medium text-text-primary">IT Support</p>
              <p className="text-sm text-text-secondary mt-1">
                Support is available through the ticket system. Create a ticket
                describing your issue and our team will assist you promptly.
              </p>
              <p className="text-xs text-text-muted mt-2">
                For general inquiries:{" "}
                <a
                  href="mailto:support@example.com"
                  className="text-primary hover:underline"
                >
                  support@example.com
                </a>
              </p>
            </div>
          </div>
          <Button asChild variant="outline">
            <Link to="/create-ticket">
              <PlusCircle className="h-4 w-4 mr-2" />
              Create Support Ticket
            </Link>
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
