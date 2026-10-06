import { useState } from "react";
import { NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import {
  LayoutDashboard,
  Ticket,
  ClipboardList,
  Bot,
  ShieldCheck,
  FileText,
  Settings,
  Users,
  LogOut,
  Menu,
  X,
  Cog,
  HelpCircle,
  Info,
} from "lucide-react";
import { useAuth } from "@/providers/auth";
import { useEvents } from "@/hooks/use-events";
import { NotificationBell } from "@/components/common/notification-bell";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { cn } from "@/lib/utils";

const NAV = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard, roles: ["admin", "user"] },
  { to: "/ai-assistant", label: "AI Assistant", icon: Bot, roles: ["admin", "user"] },
  { to: "/my-tickets", label: "My Tickets", icon: ClipboardList, roles: ["admin", "user"] },
  { to: "/tickets", label: "All Tickets", icon: Ticket, roles: ["admin"] },
  { to: "/reports", label: "Reports", icon: FileText, roles: ["admin", "user"] },
  { to: "/admin/users", label: "Users", icon: Users, roles: ["admin"] },
  { to: "/admin/system", label: "System", icon: Settings, roles: ["admin"] },
  { to: "/settings", label: "Settings", icon: Cog, roles: ["admin", "user"] },
  { to: "/help-support", label: "Help & Support", icon: HelpCircle, roles: ["admin", "user"] },
  { to: "/about", label: "About", icon: Info, roles: ["admin", "user"] },
];

function initials(name?: string | null) {
  if (!name) return "?";
  return name
    .split(" ")
    .slice(0, 2)
    .map((p) => p[0])
    .join("")
    .toUpperCase();
}

export default function AppLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [mobileOpen, setMobileOpen] = useState(false);
  const location = useLocation();
  useEvents();

  const allowed = NAV.filter((item) => user && item.roles.includes(user.role));

  return (
    <div className="flex min-h-screen bg-background">
      {mobileOpen && (
        <div
          className="fixed inset-0 z-30 bg-black/50 backdrop-blur-sm md:hidden"
          onClick={() => setMobileOpen(false)}
          aria-hidden="true"
        />
      )}

      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-40 w-64 border-r sidebar transition-all duration-300 md:translate-x-0",
          mobileOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0",
        )}
      >
        <div className="flex h-16 items-center justify-between border-b px-4">
          <div className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-blue-500 via-indigo-500 to-purple-600 shadow-md shadow-blue-500/20 text-white font-black tracking-wider text-sm">
              N
            </div>
            <div className="flex flex-col">
              <span className="text-lg font-black tracking-tight bg-gradient-to-r from-white via-blue-100 to-blue-400 bg-clip-text text-transparent">
                NEX<span className="text-blue-500">DESK</span>
              </span>
              <span className="text-[9px] font-semibold uppercase tracking-widest text-blue-400/80 -mt-1">
                AI IT Support
              </span>
            </div>
          </div>
          <Button
            variant="ghost"
            size="icon"
            className="md:hidden"
            onClick={() => setMobileOpen(false)}
          >
            <X className="h-5 w-5" />
          </Button>
        </div>

        <nav className="flex-1 overflow-y-auto space-y-1 p-3">
          {allowed.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              onClick={() => setMobileOpen(false)}
              className={({ isActive }) =>
                cn(
                  "relative flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all duration-200 sidebar-item",
                  isActive && "active",
                )
              }
            >
              <item.icon className="h-5 w-5 shrink-0" aria-hidden="true" />
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="border-t p-3">
          <div className="flex items-center gap-3 px-3">
            <Avatar className="h-9 w-9 bg-primary-muted text-primary">
              <AvatarFallback>{initials(user?.full_name)}</AvatarFallback>
            </Avatar>
            <div className="min-w-0 flex-1">
              <p className="text-sm font-medium text-text-primary truncate">
                {user?.full_name}
              </p>
              <p className="text-xs text-text-muted capitalize">
                {user?.role}
              </p>
            </div>
          </div>
        </div>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col md:ml-64">
        <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b bg-background/80 px-4 md:px-6 backdrop-blur-xl glass">
          <div className="flex items-center gap-3">
            <Button
              variant="ghost"
              size="icon"
              className="md:hidden"
              onClick={() => setMobileOpen(true)}
            >
              <Menu className="h-5 w-5" />
            </Button>
            <span className="hidden sm:block text-sm font-medium text-text-secondary">
              {allowed.find((n) => n.to === location.pathname)?.label ??
                "Helpdesk"}
            </span>
          </div>

          <div className="flex items-center gap-2">
            <NotificationBell />

            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button
                  variant="ghost"
                  className="h-10 gap-2 rounded-full bg-surface hover:bg-surface-hover px-3 pr-4"
                >
                  <Avatar className="h-8 w-8 bg-primary-muted text-primary">
                    <AvatarFallback>
                      {initials(user?.full_name)}
                    </AvatarFallback>
                  </Avatar>
                  <span className="hidden sm:block text-sm font-medium text-text-primary">
                    {user?.full_name}
                  </span>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent
                align="end"
                className="dropdown-content w-56"
              >
                <DropdownMenuLabel className="px-2 text-xs font-semibold text-text-muted uppercase tracking-wider">
                  Account
                </DropdownMenuLabel>
                <DropdownMenuItem
                  onClick={() => navigate("/settings?tab=profile")}
                  className="dropdown-item flex items-center gap-2"
                >
                  <Settings className="h-4 w-4" />
                  Profile
                </DropdownMenuItem>
                <DropdownMenuItem
                  onClick={() => navigate("/settings")}
                  className="dropdown-item flex items-center gap-2"
                >
                  <Cog className="h-4 w-4" />
                  Settings
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem
                  onClick={logout}
                  className="dropdown-item flex items-center gap-2 text-destructive"
                >
                  <LogOut className="h-4 w-4" />
                  Sign out
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </header>

        <main className="flex-1 p-4 md:p-6 lg:p-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
