import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { Bot, User, Shield, Lock, Key, CheckCircle2, AlertCircle, Mail } from "lucide-react";
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

export default function RegisterPage() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({
    full_name: "",
    email: "",
    username: "",
    department: "",
    password: "",
    confirm: "",
    admin_registration_code: "",
  });
  const [loading, setLoading] = useState(false);
  const [selectedRole, setSelectedRole] = useState<Role>("user");
  const [passwordStrength, setPasswordStrength] = useState(0);

  const set = (key: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm((f) => ({ ...f, [key]: e.target.value }));

  const calculatePasswordStrength = (password: string): number => {
    let strength = 0;
    if (password.length >= 8) strength += 1;
    if (password.length >= 12) strength += 1;
    if (/[A-Z]/.test(password)) strength += 1;
    if (/[a-z]/.test(password)) strength += 1;
    if (/[0-9]/.test(password)) strength += 1;
    if (/[^A-Za-z0-9]/.test(password)) strength += 1;
    return Math.min(strength, 4);
  };

  const handlePasswordChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setForm((f) => ({ ...f, password: value }));
    setPasswordStrength(calculatePasswordStrength(value));
  };

  const getStrengthLabel = (strength: number) => {
    if (strength <= 1) return { label: "Weak", color: "text-red-400", bg: "bg-red-400" };
    if (strength === 2) return { label: "Fair", color: "text-yellow-400", bg: "bg-yellow-400" };
    if (strength === 3) return { label: "Good", color: "text-blue-400", bg: "bg-blue-400" };
    return { label: "Strong", color: "text-green-400", bg: "bg-green-400" };
  };

  const strength = getStrengthLabel(passwordStrength);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (form.password.length < 8) {
      toast.error("Password must be at least 8 characters");
      return;
    }
    if (form.password !== form.confirm) {
      toast.error("Passwords do not match");
      return;
    }
    if (selectedRole === "admin" && !form.admin_registration_code.trim()) {
      toast.error("Admin registration code is required");
      return;
    }

    setLoading(true);
    try {
      await register({
        full_name: form.full_name,
        email: form.email,
        username: form.username,
        department: form.department || null,
        password: form.password,
        role: selectedRole,
        admin_registration_code: selectedRole === "admin" ? form.admin_registration_code : undefined,
      });
      toast.success("Account created. Welcome!");
      navigate("/");
    } catch (err: unknown) {
      toast.error(extractErrorMessage(err, "Registration failed"));
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
            <CardTitle className="text-2xl font-bold text-white">Create an account</CardTitle>
            <CardDescription className="flex items-center justify-center gap-1.5 text-[#94A3B8]">
              <Lock className="h-3.5 w-3.5" />
              Join ITDesk to manage tickets
            </CardDescription>
          </CardHeader>

          <CardContent className="space-y-4.5">
            {/* Segmented Role Selector */}
            <div className="space-y-2">
              <Label className="text-xs font-medium text-[#94A3B8] uppercase tracking-wide">Register as</Label>
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
                <Label htmlFor="full_name" className="text-sm font-medium text-[#CBD5E1]">
                  Full name
                </Label>
                <div className="auth-input-wrapper">
                  <Input
                    id="full_name"
                    autoFocus
                    value={form.full_name}
                    onChange={set("full_name")}
                    required
                    placeholder="Enter your full name"
                    className="h-[48px] bg-[#1E293B] border-[#334155] text-white placeholder-[#94A3B8] hover:border-[#475569] focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 auth-input-with-icon"
                  />
                  <User className="auth-input-icon" />
                </div>
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="email" className="text-sm font-medium text-[#CBD5E1]">
                  Email
                </Label>
                <div className="auth-input-wrapper">
                  <Input
                    id="email"
                    type="email"
                    value={form.email}
                    onChange={set("email")}
                    required
                    placeholder="Enter your email"
                    className="h-[48px] bg-[#1E293B] border-[#334155] text-white placeholder-[#94A3B8] hover:border-[#475569] focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 auth-input-with-icon"
                  />
                  <Mail className="auth-input-icon" />
                </div>
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="username" className="text-sm font-medium text-[#CBD5E1]">
                  Username
                </Label>
                <div className="auth-input-wrapper">
                  <Input
                    id="username"
                    value={form.username}
                    onChange={set("username")}
                    minLength={3}
                    required
                    placeholder="Choose a username"
                    className="h-[48px] bg-[#1E293B] border-[#334155] text-white placeholder-[#94A3B8] hover:border-[#475569] focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 auth-input-with-icon"
                  />
                  <Shield className="auth-input-icon" />
                </div>
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="department" className="text-sm font-medium text-[#CBD5E1]">
                  Department (optional)
                </Label>
                <Input
                  id="department"
                  value={form.department}
                  onChange={set("department")}
                   placeholder="e.g., IT, Operations, HR"
                  className="h-[48px] bg-[#1E293B] border-[#334155] text-white placeholder-[#94A3B8] hover:border-[#475569] focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20"
                />
              </div>

              {/* Admin Registration Code - Minimal */}
              {selectedRole === "admin" && (
                <div className="space-y-1.5">
                  <Label htmlFor="admin_registration_code" className="text-sm font-medium text-[#CBD5E1]">
                    Admin Registration Code
                  </Label>
                  <Input
                    id="admin_registration_code"
                    type="password"
                    value={form.admin_registration_code}
                    onChange={set("admin_registration_code")}
                    required
                    placeholder="Enter admin registration code"
                    className="h-[48px] bg-[#1E293B] border-[#334155] text-white placeholder-[#94A3B8] hover:border-[#475569] focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20"
                    autoComplete="off"
                  />
                  <p className="text-xs text-[#94A3B8]">
                    Contact your system administrator for the registration code.
                  </p>
                </div>
              )}

              <div className="space-y-1.5">
                <Label htmlFor="password" className="text-sm font-medium text-[#CBD5E1]">
                  Password
                </Label>
                <div className="auth-input-wrapper">
                  <Input
                    id="password"
                    type="password"
                    value={form.password}
                    onChange={handlePasswordChange}
                    required
                    placeholder="Create a password (min 8 characters)"
                    className="h-[48px] bg-[#1E293B] border-[#334155] text-white placeholder-[#94A3B8] hover:border-[#475569] focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 auth-input-with-icon"
                    autoComplete="new-password"
                  />
                  <Lock className="auth-input-icon" />
                </div>
                {/* Password Strength Meter */}
                {form.password.length > 0 && (
                  <div className="space-y-1.5">
                    <div className="h-1.5 w-full bg-[#1E293B] rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-all duration-300 ${
                          passwordStrength > 0 ? strength.bg : "bg-transparent"
                        }`}
                        style={{ width: `${(passwordStrength / 4) * 100}%` }}
                      />
                    </div>
                    <p className="text-xs font-medium text-right">{strength.label}</p>
                  </div>
                )}
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="confirm" className="text-sm font-medium text-[#CBD5E1]">
                  Confirm password
                </Label>
                <div className="auth-input-wrapper">
                  <Input
                    id="confirm"
                    type="password"
                    value={form.confirm}
                    onChange={set("confirm")}
                    required
                    placeholder="Confirm your password"
                    className="h-[48px] bg-[#1E293B] border-[#334155] text-white placeholder-[#94A3B8] hover:border-[#475569] focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 auth-input-with-icon"
                    autoComplete="new-password"
                  />
                  <Lock className="auth-input-icon" />
                </div>
                {form.confirm && form.password !== form.confirm && (
                  <p className="text-xs text-red-400 flex items-center gap-1">
                    <AlertCircle className="h-3.5 w-3.5" />
                    Passwords do not match
                  </p>
                )}
                {form.confirm && form.password === form.confirm && form.password.length >= 8 && (
                  <p className="text-xs text-green-400 flex items-center gap-1">
                    <CheckCircle2 className="h-3.5 w-3.5" />
                    Passwords match
                  </p>
                )}
              </div>

              <Button
                type="submit"
                className="w-full h-[50px] text-base font-semibold rounded-xl bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white shadow-lg shadow-blue-500/25 hover:shadow-blue-500/40 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
                disabled={loading}
              >
                {loading && <Spinner className="h-5 w-5 mr-2" />}
                Create account
              </Button>

              <p className="text-center text-sm text-[#64748B]">
                Already have an account?{" "}
                <Link to="/login" className="text-blue-400 font-medium hover:text-blue-300 hover:underline">
                  Sign in
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