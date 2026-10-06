import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { Bot, Eye, EyeOff, User, Shield, Lock, Mail } from "lucide-react";
import { useAuth } from "@/providers/auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Spinner } from "@/components/common/loading-screen";
import { cn, extractErrorMessage } from "@/lib/utils";

type Role = "admin" | "user";

const ROLE_OPTIONS: { value: Role; label: string; icon: React.ReactNode }[] = [
  { value: "user", label: "User", icon: <User className="h-4.5 w-4.5" /> },
  { value: "admin", label: "Admin", icon: <Shield className="h-4.5 w-4.5" /> },
];

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [identifier, setIdentifier] = useState("");
  const [password, setPassword] = useState("");
  const [rememberMe, setRememberMe] = useState(false);
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [selectedRole, setSelectedRole] = useState<Role>("user");

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await login(identifier, password, selectedRole);
      toast.success("Welcome back!");
      const from = (location.state as { from?: { pathname?: string } })?.from?.pathname;
      navigate(from && from !== "/login" ? from : "/");
    } catch (err: any) {
      toast.error(extractErrorMessage(err, "Invalid credentials"));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="relative min-h-screen flex items-center justify-center p-4 overflow-hidden bg-[#020617]">
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 h-80 w-80 rounded-full bg-blue-500/10 blur-3xl" />
        <div className="absolute -bottom-40 -left-40 h-80 w-80 rounded-full bg-purple-500/10 blur-3xl" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 h-96 w-96 rounded-full bg-blue-500/5 blur-3xl" />
      </div>

      <div className="relative z-10 w-full max-w-[420px]">
        <Card className="bg-[#0F172A]/80 backdrop-blur-xl border border-[#1E293B] shadow-2xl">
          <CardHeader className="text-center pb-3">
            <div className="mx-auto mb-3 flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-blue-500 to-blue-600">
              <Bot className="h-6 w-6 text-white" />
            </div>
            <CardTitle className="text-2xl font-bold text-white">Sign in to ITDesk</CardTitle>
            <CardDescription className="flex items-center justify-center gap-1.5 text-[#94A3B8]">
              <Lock className="h-3.5 w-3.5" />
              AI-assisted IT Helpdesk
            </CardDescription>
          </CardHeader>

          <CardContent className="space-y-4.5">
            {/* Segmented Role Selector */}
            <div className="space-y-2">
              <Label className="text-xs font-medium text-[#94A3B8] uppercase tracking-wide">Sign in as</Label>
              <div className="flex gap-1 bg-[#020617] p-1 rounded-xl border border-[#1E293B]">
                {ROLE_OPTIONS.map((role) => (
                  <button
                    key={role.value}
                    type="button"
                    onClick={() => setSelectedRole(role.value)}
                    className={cn(
                      "relative flex items-center justify-center gap-2 flex-1 h-[48px] rounded-lg transition-all duration-200 ease-out",
                      "focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:ring-offset-2 focus:ring-offset-[#0F172A]",
                      selectedRole === role.value
                        ? "bg-blue-500 text-white shadow-lg shadow-blue-500/30"
                        : "bg-transparent text-[#94A3B8] hover:text-[#CBD5E1] hover:bg-[#1E293B]/50"
                    )}
                  >
                    <span className="flex h-7 w-7 items-center justify-center rounded-lg">
                      {role.icon}
                    </span>
                    <span className="font-medium text-sm">{role.label}</span>
                  </button>
                ))}
              </div>
            </div>

            <form onSubmit={submit} className="space-y-4">
              <div className="space-y-1.5">
                <Label htmlFor="identifier" className="text-sm font-medium text-[#CBD5E1]">
                  Email or Username
                </Label>
                <div className="auth-input-wrapper">
                  <Input
                    id="identifier"
                    autoFocus
                    value={identifier}
                    onChange={(e) => setIdentifier(e.target.value)}
                    required
                    placeholder="Enter your email or username"
                    className="h-[48px] bg-[#1E293B] border-[#334155] text-white placeholder-[#94A3B8] hover:border-[#475569] focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 auth-input-with-icon"
                  />
                  <Mail className="auth-input-icon" />
                </div>
              </div>

              <div className="space-y-1.5">
                <div className="flex items-center justify-between">
                  <Label htmlFor="password" className="text-sm font-medium text-[#CBD5E1]">
                    Password
                  </Label>
                  <Link to="/forgot-password" className="text-xs text-blue-400 hover:text-blue-300 hover:underline">
                    Forgot password?
                  </Link>
                </div>
                <div className="auth-input-wrapper">
                  <Input
                    id="password"
                    type={showPassword ? "text" : "password"}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    placeholder="Enter your password"
                    className="h-[48px] bg-[#1E293B] border-[#334155] text-white placeholder-[#94A3B8] hover:border-[#475569] focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 auth-input-with-icon"
                  />
                  <Lock className="auth-input-icon" />
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    className="auth-input-toggle"
                    onClick={() => setShowPassword(!showPassword)}
                    aria-label={showPassword ? "Hide password" : "Show password"}
                  >
                    {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                  </Button>
                </div>
              </div>

              <div className="flex items-center justify-between">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={rememberMe}
                    onChange={(e) => setRememberMe(e.target.checked)}
                    className="h-4 w-4 rounded border-[#334155] bg-[#1E293B] text-blue-500 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-[#0F172A]"
                  />
                  <span className="text-sm text-[#94A3B8]">Remember me</span>
                </label>
              </div>

              <Button
                type="submit"
                className="w-full h-[50px] text-base font-semibold rounded-xl bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white shadow-lg shadow-blue-500/25 hover:shadow-blue-500/40 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
                disabled={loading}
              >
                {loading && <Spinner className="h-5 w-5 mr-2" />}
                Sign In
              </Button>

              <p className="text-center text-sm text-[#64748B]">
                Don't have an account?{" "}
                <Link to="/register" className="text-blue-400 font-medium hover:text-blue-300 hover:underline">
                  Register
                </Link>
              </p>
            </form>
          </CardContent>
        </Card>

        <p className="mt-4 text-center text-xs text-[#475569]">
          ITDesk — AI-powered ticket management
        </p>
      </div>
    </div>
  );
}