import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { authApi } from "@/api/endpoints";
import { setAccessToken, setUnauthorizedHandler } from "@/api/client";
import type { User } from "@/models/types";

type AuthStatus = "loading" | "authenticated" | "unauthenticated";

interface AuthContextValue {
  user: User | null;
  status: AuthStatus;
  login: (identifier: string, password: string, role?: "admin" | "user") => Promise<void>;
  register: (payload: Record<string, unknown>) => Promise<void>;
  logout: () => Promise<void>;
  setUser: (user: User | null) => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [status, setStatus] = useState<AuthStatus>("loading");
  const booted = useRef(false);

  useEffect(() => {
    if (booted.current) return;
    booted.current = true;
    authApi
      .me()
      .then((me) => {
        setUser(me);
        setStatus("authenticated");
      })
      .catch(() => {
        setStatus("unauthenticated");
      });
  }, []);

  // If any protected request gets a 401 that a refresh can't recover, treat the
  // session as expired and sign out so the user is redirected to login.
  useEffect(() => {
    setUnauthorizedHandler(() => {
      setAccessToken(null);
      setUser(null);
      setStatus("unauthenticated");
    });
    return () => setUnauthorizedHandler(null);
  }, []);

  const login = useCallback(async (identifier: string, password: string, role?: "admin" | "user") => {
    const res = await authApi.login(identifier, password, role);
    setAccessToken(res.access_token);
    setUser(res.user);
    setStatus("authenticated");
  }, []);

  const register = useCallback(async (payload: Record<string, unknown>) => {
    const res = await authApi.register(payload);
    setAccessToken(res.access_token);
    setUser(res.user);
    setStatus("authenticated");
  }, []);

  const logout = useCallback(async () => {
    try {
      await authApi.logout();
    } finally {
      setAccessToken(null);
      setUser(null);
      setStatus("unauthenticated");
    }
  }, []);

  return (
    <AuthContext.Provider
      value={{ user, status, login, register, logout, setUser }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}