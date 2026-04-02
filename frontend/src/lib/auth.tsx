import React from "react";
import { apiFetch } from "./api";

type User = { id: string; email: string; name: string; created_at: string };

type AuthState = {
  user: User | null;
  token: string | null;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, name: string) => Promise<void>;
  logout: () => void;
  refreshMe: () => Promise<void>;
};

const AuthContext = React.createContext<AuthState | null>(null);

function getStoredToken() {
  return localStorage.getItem("mw_token");
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setToken] = React.useState<string | null>(getStoredToken());
  const [user, setUser] = React.useState<User | null>(null);

  const refreshMe = React.useCallback(async () => {
    if (!getStoredToken()) {
      setUser(null);
      return;
    }
    const me = await apiFetch<User>("/api/auth/me");
    setUser(me);
  }, []);

  React.useEffect(() => {
    refreshMe().catch(() => setUser(null));
  }, [refreshMe, token]);

  const login = React.useCallback(async (email: string, password: string) => {
    const res = await apiFetch<{ access_token: string }>("/api/auth/login", {
      method: "POST",
      auth: false,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    localStorage.setItem("mw_token", res.access_token);
    setToken(res.access_token);
    await refreshMe();
  }, [refreshMe]);

  const register = React.useCallback(async (email: string, password: string, name: string) => {
    await apiFetch<User>("/api/auth/register", {
      method: "POST",
      auth: false,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password, name }),
    });
    await login(email, password);
  }, [login]);

  const logout = React.useCallback(() => {
    localStorage.removeItem("mw_token");
    setToken(null);
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, token, login, register, logout, refreshMe }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = React.useContext(AuthContext);
  if (!ctx) throw new Error("AuthProvider missing");
  return ctx;
}

