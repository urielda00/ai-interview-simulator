import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { authService } from "../services/authService";

const AUTH_STORAGE_KEY = "ai_interview_auth_token";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem(AUTH_STORAGE_KEY) || "");
  const [user, setUser] = useState(null);
  const [isBootstrapping, setIsBootstrapping] = useState(true);

  const persistToken = useCallback((nextToken) => {
    if (nextToken) {
      localStorage.setItem(AUTH_STORAGE_KEY, nextToken);
    } else {
      localStorage.removeItem(AUTH_STORAGE_KEY);
    }
    setToken(nextToken || "");
  }, []);

  const logout = useCallback(() => {
    persistToken("");
    setUser(null);
  }, [persistToken]);

  const refreshMe = useCallback(async () => {
    if (!token) {
      setUser(null);
      setIsBootstrapping(false);
      return null;
    }

    try {
      const me = await authService.getMe(token);
      setUser(me);
      return me;
    } catch (error) {
      logout();
      return null;
    } finally {
      setIsBootstrapping(false);
    }
  }, [token, logout]);

  const login = useCallback(
    async ({ email, password }) => {
      const data = await authService.login({ email, password });
      persistToken(data.access_token);
      const me = await authService.getMe(data.access_token);
      setUser(me);
      return me;
    },
    [persistToken]
  );

  const register = useCallback(async ({ email, password, full_name }) => {
    return authService.register({ email, password, full_name });
  }, []);

  useEffect(() => {
    refreshMe();
  }, [refreshMe]);

  const value = useMemo(
    () => ({
      token,
      user,
      isAuthenticated: Boolean(token && user),
      isBootstrapping,
      login,
      register,
      logout,
      refreshMe,
    }),
    [token, user, isBootstrapping, login, register, logout, refreshMe]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }

  return context;
}