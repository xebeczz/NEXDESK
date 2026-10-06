import { useState } from "react";
import { toast } from "sonner";
import { FileText, Download, Loader2, ShieldCheck, PieChart, Clock3, TrendingUp, BarChart3 } from "lucide-react";
import { reportsApi, type ReportType } from "@/api/endpoints";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { downloadBlob, extractErrorMessage } from "@/lib/utils";

interface ReportDef {
  type: ReportType;
  title: string;
  description: string;
  icon: React.ReactNode;
}

const REPORTS: ReportDef[] = [
  {
    type: "summary",
    title: "Summary report",
    description: "Overall ticket counts, statuses, priorities, and SLA compliance.",
    icon: <FileText />,
  },
  {
    type: "analytics",
    title: "Analytics overview",
    description: "Department distribution, SLA status, and activity highlights.",
    icon: <BarChart3 />,
  },
  {
    type: "resolution",
    title: "Resolution times",
    description: "Average resolution time and SLA breach detail per priority.",
    icon: <Clock3 />,
  },
  {
    type: "priority",
    title: "Priority analysis",
    description: "Tickets grouped by priority with workload context.",
    icon: <PieChart />,
  },
  {
    type: "monthly",
    title: "Monthly trends",
    description: "Ticket creation trend over the last 12 months.",
    icon: <TrendingUp />,
  },
];

export default function ReportsPage() {
  const [busy, setBusy] = useState<ReportType | null>(null);

  const download = async (def: ReportDef) => {
    setBusy(def.type);
    try {
      const res = await reportsApi.download(def.type);
      downloadBlob(res.data as Blob, `itdesk-${def.type}-report.pdf`);
      toast.success("Report downloaded");
    } catch (e: any) {
      toast.error(extractErrorMessage(e, "Failed to generate report"));
    } finally {
      setBusy(null);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Reports</h1>
        <p className="flex items-center gap-1 text-sm text-muted-foreground">
          <ShieldCheck className="h-3.5 w-3.5" /> Generated as PDF from live ticket data
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {REPORTS.map((def) => (
          <Card key={def.type} className="flex flex-col">
            <CardHeader>
              <div className="mb-2 flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 text-primary">
                {def.icon}
              </div>
              <CardTitle className="text-base">{def.title}</CardTitle>
              <CardDescription>{def.description}</CardDescription>
            </CardHeader>
            <CardContent className="mt-auto">
              <Button className="w-full" onClick={() => download(def)} disabled={busy !== null}>
                {busy === def.type ? <Loader2 className="animate-spin" /> : <Download />}
                Download PDF
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}