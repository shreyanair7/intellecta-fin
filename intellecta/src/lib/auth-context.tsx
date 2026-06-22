import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { api, type User } from "./api";

type AuthCtx = {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  signUp: (name: string, email: string, password: string) => Promise<void>;
  logout: () => void;
};

const Ctx = createContext<AuthCtx | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const s = api.getSession();
    if (s) setUser({ id: s.id, name: s.name, email: s.email });
    setLoading(false);
  }, []);

  const login = async (email: string, password: string) => {
    const u = await api.logIn(email, password);
    setUser(u);
  };
  const signUp = async (name: string, email: string, password: string) => {
    const u = await api.signUp(name, email, password);
    setUser(u);
  };
  const logout = () => { api.logOut(); setUser(null); };

  return <Ctx.Provider value={{ user, loading, login, signUp, logout }}>{children}</Ctx.Provider>;
}

export const useAuth = () => {
  const v = useContext(Ctx);
  if (!v) throw new Error("useAuth must be used within AuthProvider");
  return v;
};
