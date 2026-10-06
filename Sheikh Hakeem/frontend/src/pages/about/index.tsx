import { Link } from "react-router-dom";
import {
  Info,
  ArrowLeft,
  Bot,
  Ticket,
  Brain,
  Search,
  Tags,
  Zap,
  Building2,
  BarChart3,
  CheckCircle2,
  Layers,
  FileText,
  MessageSquare,
  ClipboardList,
  GitBranch,
  Server,
  Shield,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";

const STEPS = [
  {
    icon: FileText,
    title: "Report Issue",
    description: "Describe your IT problem in detail through the ticket form.",
  },
  {
    icon: Brain,
    title: "AI Analysis",
    description: "Our AI analyzes the issue to understand the root cause.",
  },
  {
    icon: Tags,
    title: "Category / Priority / Department",
    description: "The system automatically assigns the correct category, priority, and department.",
  },
  {
    icon: Search,
    title: "Similar Ticket Detection",
    description: "Finds previously resolved tickets with similar symptoms.",
  },
  {
    icon: MessageSquare,
    title: "Solution Recommendation",
    description: "Provides step-by-step troubleshooting guidance.",
  },
  {
    icon: ClipboardList,
    title: "Ticket Tracking",
    description: "Track the progress of your ticket from creation to resolution.",
  },
  {
    icon: CheckCircle2,
    title: "Resolution",
    description: "Issue is resolved and documented for future reference.",
  },
];

const FEATURES = [
  {
    icon: Bot,
    title: "AI IT Assistant",
    description: "Intelligent chatbot that diagnoses IT issues and suggests solutions.",
  },
  {
    icon: Ticket,
    title: "Ticket Management",
    description: "Create, track, and manage support tickets with full status visibility.",
  },
  {
    icon: Brain,
    title: "AI Analysis",
    description: "Automatic root cause analysis and issue classification.",
  },
  {
    icon: Search,
    title: "Similar Tickets",
    description: "Find resolved tickets matching your current issue.",
  },
  {
    icon: Tags,
    title: "Smart Categorization",
    description: "Auto-assigns category, priority, and department.",
  },
  {
    icon: Zap,
    title: "Priority Detection",
    description: "AI determines the urgency based on impact and severity.",
  },
  {
    icon: Building2,
    title: "Department Routing",
    description: "Tickets are automatically routed to the right team.",
  },
  {
    icon: BarChart3,
    title: "Reports & Analytics",
    description: "Track ticket trends, SLA compliance, and team performance.",
  },
];

const TECH = [
  { icon: Layers, name: "React 19", description: "Frontend UI library" },
  { icon: Server, name: "FastAPI", description: "Backend API framework" },
  { icon: GitBranch, name: "TypeScript", description: "Type-safe development" },
  { icon: Shield, name: "JWT Auth", description: "Secure authentication" },
  { icon: Brain, name: "AI Integration", description: "Intelligent analysis" },
  { icon: Ticket, name: "SQLAlchemy", description: "Database ORM" },
];

export default function AboutPage() {
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
            <Info className="h-6 w-6 text-primary" />
            About NexDesk
          </h1>
          <p className="page-subtitle">
            AI-powered IT support and ticket management system.
          </p>
        </div>
      </div>

      {/* Description */}
      <Card className="card-elevated">
        <CardContent className="pt-6">
          <p className="text-text-secondary leading-relaxed">
            NexDesk is an AI-powered IT support and ticket management system
            designed to help users report, analyze, track and resolve IT issues
            efficiently. By combining intelligent analysis with streamlined
            ticket workflows, NexDesk reduces resolution time and improves
            support quality.
          </p>
        </CardContent>
      </Card>

      {/* About the System */}
      <Card className="card-elevated">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Layers className="h-5 w-5 text-primary" />
            About the System
          </CardTitle>
          <CardDescription>
            NexDesk helps users manage the complete IT support lifecycle.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-3 sm:grid-cols-2">
            {[
              "Report IT issues through an intuitive ticket form",
              "Analyze problems using AI-powered diagnosis",
              "Identify root causes automatically",
              "Determine the correct category for each issue",
              "Assign appropriate priority levels",
              "Route tickets to the right department",
              "Find similar resolved tickets for reference",
              "Get step-by-step troubleshooting recommendations",
              "Track ticket status from creation to resolution",
            ].map((item, i) => (
              <div key={i} className="flex items-start gap-2">
                <CheckCircle2 className="h-4 w-4 mt-0.5 shrink-0 text-success" />
                <span className="text-sm text-text-secondary">{item}</span>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* How NexDesk Works */}
      <Card className="card-elevated">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Zap className="h-5 w-5 text-primary" />
            How NexDesk Works
          </CardTitle>
          <CardDescription>
            A step-by-step overview of the support workflow.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {STEPS.map((step, i) => (
              <div key={step.title} className="flex items-start gap-4">
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary font-bold text-sm">
                  {i + 1}
                </div>
                <div className="flex-1 pt-1">
                  <div className="flex items-center gap-2">
                    <step.icon className="h-4 w-4 text-primary" />
                    <p className="text-sm font-medium text-text-primary">
                      {step.title}
                    </p>
                  </div>
                  <p className="text-sm text-text-muted mt-1">
                    {step.description}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Key Features */}
      <Card className="card-elevated">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Layers className="h-5 w-5 text-primary" />
            Key Features
          </CardTitle>
          <CardDescription>
            Core capabilities of the NexDesk platform.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {FEATURES.map((feature) => (
              <div
                key={feature.title}
                className="flex flex-col items-center gap-2 rounded-lg border border-border p-4 text-center bg-surface/50 hover:bg-surface transition-colors"
              >
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
                  <feature.icon className="h-5 w-5 text-primary" />
                </div>
                <p className="text-sm font-medium text-text-primary">
                  {feature.title}
                </p>
                <p className="text-xs text-text-muted">{feature.description}</p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Technology */}
      <Card className="card-elevated">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Server className="h-5 w-5 text-primary" />
            Technology
          </CardTitle>
          <CardDescription>
            Technologies powering NexDesk.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {TECH.map((t) => (
              <div
                key={t.name}
                className="flex items-center gap-3 rounded-lg border border-border p-3 bg-surface/50"
              >
                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-primary/10">
                  <t.icon className="h-4 w-4 text-primary" />
                </div>
                <div>
                  <p className="text-sm font-medium text-text-primary">{t.name}</p>
                  <p className="text-xs text-text-muted">{t.description}</p>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Back to Dashboard */}
      <div className="flex justify-center pt-2 pb-4">
        <Button asChild variant="outline">
          <Link to="/">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Dashboard
          </Link>
        </Button>
      </div>
    </div>
  );
}
