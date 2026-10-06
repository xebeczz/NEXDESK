import { BrowserRouter } from "react-router-dom";
import { Toaster } from "sonner";
import { ThemeProvider } from "@/providers/theme";
import { QueryProvider } from "@/providers/query";
import { AuthProvider } from "@/providers/auth";
import AppRoutes from "@/routes";

export default function App() {
  return (
    <BrowserRouter>
      <ThemeProvider>
        <QueryProvider>
          <AuthProvider>
            <AppRoutes />
            <Toaster richColors position="top-right" />
          </AuthProvider>
        </QueryProvider>
      </ThemeProvider>
    </BrowserRouter>
  );
}