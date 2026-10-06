import {
  createContext,
  useContext,
  useEffect,
  type ReactNode,
} from "react";

interface ThemeContextValue {
  resolvedTheme: "dark";
  setTheme: (theme: "dark") => void;
}

const ThemeContext = createContext<ThemeContextValue | undefined>(undefined);

export function ThemeProvider({ children }: { children: ReactNode }) {
  useEffect(() => {
    const root = document.documentElement;
    root.classList.remove("light", "dark");
    root.classList.add("dark");
  }, []);

  const setTheme = (theme: "dark") => {
    const root = document.documentElement;
    root.classList.remove("light", "dark");
    root.classList.add(theme);
  };

  return (
    <ThemeContext.Provider value={{ resolvedTheme: "dark", setTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const ctx = useContext(ThemeContext);
  if (!ctx) throw new Error("useTheme must be used within ThemeProvider");
  return ctx;
}
