import { useRouter } from "next/router";
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import * as api from "./api";
import type { LoginBody, RegisterBody } from "./types";

interface AuthState {
  token: string | null;
  // false until the stored token has been read on the client
  ready: boolean;
  login: (body: LoginBody) => Promise<void>;
  register: (body: RegisterBody) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const router = useRouter();
  const [token, setTokenState] = useState<string | null>(null);
  const [ready, setReady] = useState(false);

  const logout = useCallback(() => {
    api.setToken(null);
    setTokenState(null);
    void router.replace("/login");
  }, [router]);

  useEffect(() => {
    // localStorage only exists in the browser, so the token is read after mount
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setTokenState(api.getToken());
    setReady(true);
  }, []);

  useEffect(() => {
    api.setUnauthorizedHandler(logout);
    return () => api.setUnauthorizedHandler(null);
  }, [logout]);

  const login = useCallback(async (body: LoginBody) => {
    const { token } = await api.login(body);
    api.setToken(token);
    setTokenState(token);
  }, []);

  const register = useCallback(async (body: RegisterBody) => {
    const { token } = await api.register(body);
    api.setToken(token);
    setTokenState(token);
  }, []);

  const value = useMemo(
    () => ({ token, ready, login, register, logout }),
    [token, ready, login, register, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
}

// For pages behind login: sends signed-out visitors to /login and reports whether to render
export function useRequireAuth(): boolean {
  const { token, ready } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (ready && !token) void router.replace(`/login?next=${encodeURIComponent(router.asPath)}`);
  }, [ready, token, router]);

  return ready && token !== null;
}
