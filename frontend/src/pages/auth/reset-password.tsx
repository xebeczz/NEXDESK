import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { toast } from "sonner";
import { Bot, ShieldCheck, Lock, ArrowLeft, CheckCircle2, AlertCircle, Mail } from "lucide-react";
import { authApi } from "@/api/endpoints";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Spinner } from "@/components/common/loading-screen";
import { extractErrorMessage } from "@/lib/utils";

export default function ResetPasswordPage() {
  const { token } = useParams();
  const navigate = useNavigate();
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [passwordStrength, setPasswordStrength] = useState(0);

  const calculatePasswordStrength = (pwd: string): number => {
    let strength = 0;
    if (pwd.length >= 8) strength += 1;
    if (pwd.length >= 12) strength += 1;
    if (/[A-Z]/.test(pwd)) strength += 1;
    if (/[a-z]/.test(pwd)) strength += 1;
    if (/[0-9]/.test(pwd)) strength += 1;
    if (/[^A-Za-z0-9]/.test(pwd)) strength += 1;
    return Math.min(strength, 4);
  };

  const handlePasswordChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setPassword(value);
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
    setError(null);
    if (password.length < 8) {
      setError("Password must be at least 8 characters");
      return;
    }
    if (password !== confirm) {
      setError("Passwords do not match");
      return;
    }
    setLoading(true);
    try {
      await authApi.resetPassword(token ?? "", password);
      toast.success("Password reset. Please sign in.");
      navigate("/login");
    } catch (err: any) {
      setError(extractErrorMessage(err, "Reset failed"));
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
              <Lock className="h-6 w-6 text-white" />
            </div>
            <CardTitle className="text-2xl font-bold text-white">Set a new password</CardTitle>
            <CardDescription className="flex items-center justify-center gap-1.5 text-[#94A3B8]">
              <ShieldCheck className="h-3.5 w-3.5" />
              Choose a new password for your account
            </CardDescription>
          </CardHeader>

          <CardContent className="space-y-4.5">
            <form onSubmit={submit} className="space-y-4">
              <div className="space-y-1.5">
                <Label htmlFor="password" className="text-sm font-medium text-[#CBD5E1]">
                  New password
                </Label>
                <div className="relative">
                  <Input
                    id="password"
                    type="password"
                    value={password}
                    onChange={handlePasswordChange}
                    required
                    placeholder="Create a new password (min 8 characters)"
                    className="h-[48px] bg-[#1E293B] border-[#334155] text-white placeholder-[#94A3B8] hover:border-[#475569] focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 pl-12"
                    autoComplete="new-password"
                    autoFocus
                  />
                  <Lock className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-[#94A3B8] pointer-events-none" />
                </div>
                {/* Password Strength Meter */}
                {password.length > 0 && (
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
                <Input
                  id="confirm"
                  type="password"
                  value={confirm}
                  onChange={(e) => setConfirm(e.target.value)}
                  required
                  placeholder="Confirm your new password"
                  className="h-[48px] bg-[#1E293B] border-[#334155] text-white placeholder-[#94A3B8] hover:border-[#475569] focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20"
                  autoComplete="new-password"
                />
                {confirm && password !== confirm && (
                  <p className="text-xs text-red-400 flex items-center gap-1">
                    <AlertCircle className="h-3.5 w-3.5" />
                    Passwords do not match
                  </p>
                )}
                {confirm && password === confirm && password.length >= 8 && (
                  <p className="text-xs text-green-400 flex items-center gap-1">
                    <CheckCircle2 className="h-3.5 w-3.5" />
                    Passwords match
                  </p>
                )}
              </div>

              {error && (
                <div className="rounded-lg border border-red-500/30 bg-red-500/10 p-3 flex items-center gap-2 text-sm text-red-400">
                  <AlertCircle className="h-4 w-4 shrink-0" />
                  {error}
                </div>
              )}

              <Button
                type="submit"
                className="w-full h-[50px] text-base font-semibold rounded-xl bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white shadow-lg shadow-blue-500/25 hover:shadow-blue-500/40 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
                disabled={loading}
              >
                {loading && <Spinner className="h-5 w-5 mr-2" />}
                Reset password
              </Button>

              <p className="text-center text-sm text-[#64748B]">
                <Link to="/login" className="text-blue-400 font-medium hover:text-blue-300 hover:underline flex items-center justify-center gap-1">
                  <ArrowLeft className="h-4 w-4" />
                  Back to sign in
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