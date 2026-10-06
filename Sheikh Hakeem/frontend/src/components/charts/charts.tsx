import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  Legend,
  AreaChart,
  Area,
} from "recharts";
import { cn } from "@/lib/utils";

export const CHART_COLORS = [
  "#3B82F6",
  "#22C55E",
  "#F59E0B",
  "#EF4444",
  "#8B5CF6",
  "#06B6D4",
  "#EC4899",
  "#F97316",
];

export const CHART_GRADIENTS = [
  "url(#gradient-primary)",
  "url(#gradient-success)",
  "url(#gradient-warning)",
  "url(#gradient-danger)",
  "url(#gradient-purple)",
  "url(#gradient-cyan)",
  "url(#gradient-pink)",
  "url(#gradient-orange)",
];

interface Point {
  name?: string;
  count?: number;
  value?: number;
  date?: string;
  month?: string;
  [key: string]: unknown;
}

function useAxisColor() {
  return {
    grid: "rgba(148, 163, 184, 0.1)",
    text: "var(--muted-foreground)",
  };
}

export function TicketTrendChart({ data }: { data: { date: string; count: number }[] }) {
  const c = useAxisColor();
  const hasData = data.some((d) => d.count > 0);
  if (!hasData) {
    return (
      <div className="flex h-[280px] items-center justify-center text-center">
        <p className="text-sm text-muted-foreground">No ticket data available yet</p>
      </div>
    );
  }
  return (
    <ResponsiveContainer width="100%" height={280}>
      <AreaChart data={data} margin={{ top: 8, right: 16, left: -8, bottom: 0 }}>
        <defs>
          <linearGradient id="gradient-primary" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#3B82F6" stopOpacity={0.3} />
            <stop offset="100%" stopColor="#3B82F6" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid stroke={c.grid} strokeDasharray="4 4" vertical={false} />
        <XAxis
          dataKey="date"
          stroke={c.text}
          fontSize={11}
          tickFormatter={(d: string) => d.slice(5)}
          tickLine={false}
          axisLine={false}
        />
        <YAxis
          stroke={c.text}
          fontSize={11}
          allowDecimals={false}
          tickLine={false}
          axisLine={false}
          tickCount={4}
        />
        <Tooltip
          contentStyle={{
            background: "var(--card)",
            border: "1px solid var(--border)",
            borderRadius: "12px",
            boxShadow: "var(--shadow-xl)",
            padding: "12px 16px",
          }}
          labelFormatter={(d: any) => String(d ?? "").slice(5)}
          formatter={(value: any) => [value, "Tickets"]}
        />
        <Area
          type="monotone"
          dataKey="count"
          stroke="#3B82F6"
          strokeWidth={2}
          fill="url(#gradient-primary)"
          fillOpacity={1}
        />
        <Line
          type="monotone"
          dataKey="count"
          stroke="#3B82F6"
          strokeWidth={2}
          dot={false}
          isAnimationActive={true}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}

export function MonthlyBarChart({ data }: { data: { month: string; count: number }[] }) {
  const c = useAxisColor();
  const hasData = data.some((d) => d.count > 0);
  if (!hasData) {
    return (
      <div className="flex h-[280px] items-center justify-center text-center">
        <p className="text-sm text-muted-foreground">No ticket data available yet</p>
      </div>
    );
  }
  return (
    <ResponsiveContainer width="100%" height={280}>
      <BarChart data={data} margin={{ top: 8, right: 16, left: -8, bottom: 0 }}>
        <defs>
          <linearGradient id="gradient-success" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#22C55E" stopOpacity={0.8} />
            <stop offset="100%" stopColor="#22C55E" stopOpacity={0.3} />
          </linearGradient>
        </defs>
        <CartesianGrid stroke={c.grid} strokeDasharray="4 4" vertical={false} />
        <XAxis
          dataKey="month"
          stroke={c.text}
          fontSize={11}
          tickLine={false}
          axisLine={false}
          tickFormatter={(d: string) => {
            const parts = d.split("-");
            const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
            const m = parseInt(parts[1] ?? "1", 10);
            return months[m - 1] ?? parts.slice(0, 3);
          }}
        />
        <YAxis
          stroke={c.text}
          fontSize={11}
          allowDecimals={false}
          tickLine={false}
          axisLine={false}
          tickCount={4}
        />
        <Tooltip
          cursor={{ fill: "rgba(148, 163, 184, 0.1)", strokeDasharray: "4 4" }}
          contentStyle={{
            background: "var(--card)",
            border: "1px solid var(--border)",
            borderRadius: "12px",
            boxShadow: "var(--shadow-xl)",
            padding: "12px 16px",
          }}
          formatter={(value: any) => [value, "Tickets"]}
        />
        <Bar
          dataKey="count"
          fill="url(#gradient-success)"
          radius={[6, 6, 0, 0]}
          maxBarSize={40}
        />
      </BarChart>
    </ResponsiveContainer>
  );
}

export function DonutChart({ data }: { data: { name: string; value: number }[] }) {
  const total = data.reduce((sum, d) => sum + d.value, 0);

  if (!data.length || total === 0) {
    return (
      <div className="flex h-[280px] items-center justify-center text-center">
        <p className="text-sm text-muted-foreground">No ticket data available yet</p>
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={280}>
      <PieChart>
        <Pie
          data={data}
          dataKey="value"
          nameKey="name"
          innerRadius={60}
          outerRadius={95}
          paddingAngle={3}
          stroke="none"
          startAngle={90}
          endAngle={450}
        >
          {data.map((_, i) => (
            <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />
          ))}
        </Pie>
        <Tooltip
          contentStyle={{
            background: "var(--card)",
            border: "1px solid var(--border)",
            borderRadius: "12px",
            boxShadow: "var(--shadow-xl)",
            padding: "12px 16px",
          }}
          formatter={(value: any) => [value, "Tickets"]}
        />
        <Legend
          iconType="circle"
          iconSize={8}
          layout="vertical"
          align="right"
          verticalAlign="middle"
          wrapperStyle={{ paddingRight: 20 }}
        />
      </PieChart>
    </ResponsiveContainer>
  );
}

export function StatusBarChart({ data }: { data: { name: string; count: number }[] }) {
  const c = useAxisColor();

  const hasData = data.some((d) => d.count > 0);
  if (!hasData) {
    return (
      <div className="flex h-[280px] items-center justify-center text-center">
        <p className="text-sm text-muted-foreground">No ticket data available yet</p>
      </div>
    );
  }

  const getColor = (name: string) => {
    const n = name.toLowerCase();
    if (n.includes("open")) return "#3B82F6";
    if (n.includes("progress")) return "#F59E0B";
    if (n.includes("pending")) return "#06B6D4";
    if (n.includes("resolved")) return "#22C55E";
    if (n.includes("closed")) return "#64748B";
    if (n.includes("within")) return "#22C55E";
    if (n.includes("risk")) return "#F59E0B";
    if (n.includes("breach")) return "#EF4444";
    return CHART_COLORS[0];
  };

  return (
    <ResponsiveContainer width="100%" height={280}>
      <BarChart data={data} layout="vertical" margin={{ top: 4, right: 16, left: 8, bottom: 0 }}>
        <CartesianGrid stroke={c.grid} strokeDasharray="4 4" horizontal={false} />
        <XAxis type="number" stroke={c.text} fontSize={11} allowDecimals={false} tickLine={false} axisLine={false} tickCount={3} />
        <YAxis
          dataKey="name"
          type="category"
          stroke={c.text}
          fontSize={12}
          tickLine={false}
          axisLine={false}
          width={100}
        />
        <Tooltip
          cursor={false}
          contentStyle={{
            background: "var(--card)",
            border: "1px solid var(--border)",
            borderRadius: "12px",
            boxShadow: "var(--shadow-xl)",
            padding: "12px 16px",
          }}
          formatter={(value: any) => [value, "Tickets"]}
        />
        <Bar
          dataKey="count"
          radius={[0, 6, 6, 0]}
          maxBarSize={32}
        >
          {data.map((entry, i) => (
            <Cell key={i} fill={getColor(entry.name)} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}