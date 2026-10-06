import { useState } from "react";
import { Link } from "react-router-dom";
import { toast } from "sonner";
import { Bot, ShieldCheck, Mail, ArrowLeft, CheckCircle2 } from "lucide-react";
import { authApi } from "@/api/endpoints";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Spinner } from "@/components/common/loading-screen";
import { extractErrorMessage } from "@/lib/utils";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await authApi.forgotPassword(email);
      setSent(true);
    } catch (err: any) {
      toast.error(extractErrorMessage(err, "Something went wrong"));
    } finally {
      setLoading(false);
    }
  };

  if (sent) {
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
              <div className="mx-auto mb-3 flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-green-500 to-emerald-600">
                <CheckCircle2 className="h-6 w-6 text-white" />
              </div>
              <CardTitle className="text-2xl font-bold text-white">Check your email</CardTitle>
              <CardDescription className="flex items-center justify-center gap-1.5 text-[#94A3B8]">
                <Mail className="h-3.5 w-3.5" />
                Reset link sent
              </CardDescription>
            </CardHeader>

            <CardContent className="space-y-4.5 text-center">
              <div className="rounded-xl border border-[#334155] bg-[#020617]/50 p-5">
                <p className="text-[#CBD5E1] leading-relaxed">
                  If an account exists for <strong className="text-white">{email}</strong>, a password-reset link has been sent.
                </p>
                <p className="mt-3 text-sm text-[#64748B]">
                  In development the reset link is logged to the backend console.
                </p>
              </div>

              <Button
                variant="outline"
                className="w-full border-[#334155] text-[#CBD5E1] hover:border-blue-500 hover:text-blue-400 hover:bg-blue-500/5"
                onClick={() => window.location.href = "/login"}
              >
                <ArrowLeft className="h-4 w-4 mr-2" />
                Back to sign in
              </Button>
            </CardContent>
          </Card>

          <p className="mt-4 text-center text-xs text-[#475569]">
            ITDesk — AI-powered ticket management
          </p>
        </div>
      </div>
    );
  }

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
            <CardTitle className="text-2xl font-bold text-white">Reset password</CardTitle>
            <CardDescription className="flex items-center justify-center gap-1.5 text-[#94A3B8]">
              <Mail className="h-3.5 w-3.5" />
              Enter your email to receive a reset link
            </CardDescription>
          </CardHeader>

          <CardContent className="space-y-4.5">
            <form onSubmit={submit} className="space-y-4">
              <div className="space-y-1.5">
                <Label htmlFor="email" className="text-sm font-medium text-[#CBD5E1]">
                  Email
                </Label>
                <div className="relative">
                  <Input
                    id="email"
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    placeholder="Enter your email address"
                    className="h-[48px] bg-[#1E293B] border-[#334155] text-white placeholder-[#94A3B8] hover:border-[#475569] focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 pl-12"
                    autoFocus
                  />
                  <Mail className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-[#94A3B8] pointer-events-none" />
                </div>
              </div>

              <Button
                type="submit"
                className="w-full h-[50px] text-base font-semibold rounded-xl bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white shadow-lg shadow-blue-500/25 hover:shadow-blue-500/40 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
                disabled={loading}
              >
                {loading && <Spinner className="h-5 w-5 mr-2" />}
                Send reset link
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