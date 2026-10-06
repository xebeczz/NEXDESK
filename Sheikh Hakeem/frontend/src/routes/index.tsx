import { lazy, Suspense } from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import { LoadingScreen } from "@/components/common/loading-screen";
import AppLayout from "@/layouts/app-layout";
import { ProtectedRoute, GuestRoute, RoleRoute } from "@/routes/guards";

const DashboardPage = lazy(() => import("@/pages/dashboard"));
const TicketsPage = lazy(() => import("@/pages/tickets/index"));
const TicketDetailPage = lazy(() => import("@/pages/tickets/detail"));
const MyTicketsPage = lazy(() => import("@/pages/my-tickets/index"));
const AiAssistantPage = lazy(() => import("@/pages/ai-assistant/index"));
const ReportsPage = lazy(() => import("@/pages/reports/index"));
const UsersPage = lazy(() => import("@/pages/admin/users"));
const SystemPage = lazy(() => import("@/pages/admin/system"));
const SettingsPage = lazy(() => import("@/pages/settings"));
const HelpSupportPage = lazy(() => import("@/pages/help-support"));
const AboutPage = lazy(() => import("@/pages/about"));
const CreateTicketPage = lazy(() => import("@/pages/tickets/create"));
const LoginPage = lazy(() => import("@/pages/auth/login"));
const RegisterPage = lazy(() => import("@/pages/auth/register"));
const ForgotPasswordPage = lazy(() => import("@/pages/auth/forgot-password"));
const ResetPasswordPage = lazy(() => import("@/pages/auth/reset-password"));

function Page({ children }: { children: React.ReactNode }) {
  return <Suspense fallback={<LoadingScreen />}>{children}</Suspense>;
}

export default function AppRoutes() {
  return (
    <Routes>
      {/* Public */}
      <Route
        path="/login"
        element={
          <GuestRoute>
            <Page><LoginPage /></Page>
          </GuestRoute>
        }
      />
      <Route
        path="/register"
        element={
          <GuestRoute>
            <Page><RegisterPage /></Page>
          </GuestRoute>
        }
      />
      <Route
        path="/forgot-password"
        element={
          <GuestRoute>
            <Page><ForgotPasswordPage /></Page>
          </GuestRoute>
        }
      />
      <Route
        path="/reset-password/:token"
        element={
          <GuestRoute>
            <Page><ResetPasswordPage /></Page>
          </GuestRoute>
        }
      />

      {/* Authenticated app */}
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <Page><AppLayout /></Page>
          </ProtectedRoute>
        }
      >
        <Route index element={<DashboardPage />} />
        <Route path="my-tickets" element={<MyTicketsPage />} />
        <Route
          path="tickets"
          element={
            <RoleRoute roles={["admin"]}>
              <TicketsPage />
            </RoleRoute>
          }
        />
        <Route path="tickets/:id" element={<TicketDetailPage />} />
        <Route path="ai-assistant" element={<AiAssistantPage />} />
        <Route
          path="reports"
          element={
            <RoleRoute roles={["admin", "user"]}>
              <ReportsPage />
            </RoleRoute>
          }
        />
        <Route
          path="admin/users"
          element={
            <RoleRoute roles={["admin"]}>
              <UsersPage />
            </RoleRoute>
          }
        />
        <Route
          path="admin/system"
          element={
            <RoleRoute roles={["admin"]}>
              <SystemPage />
            </RoleRoute>
          }
        />
        <Route
          path="settings"
          element={<SettingsPage />}
        />
        <Route
          path="help-support"
          element={<HelpSupportPage />}
        />
        <Route
          path="about"
          element={<AboutPage />}
        />
        <Route
          path="create-ticket"
          element={<CreateTicketPage />}
        />
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}