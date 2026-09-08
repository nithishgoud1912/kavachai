"use client";

import { useState, useCallback, useEffect } from "react";
import type { Session } from "@/app/types";

export interface SessionState {
  session: Session | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (session: Session) => void;
  logout: () => void;
}

const STORAGE_KEY = "kavachai_session";
const SESSION_ID_KEY = "kavachai_session_id";

export function useSession(): SessionState {
  const [session, setSession] = useState<Session | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    try {
      const stored = sessionStorage.getItem(STORAGE_KEY);
      if (stored) {
        setSession(JSON.parse(stored));
      }
    } catch {
      // Ignore sessionStorage parsing errors
    } finally {
      setIsLoading(false);
    }
  }, []);

  const login = useCallback((newSession: Session) => {
    setSession(newSession);
    try {
      sessionStorage.setItem(STORAGE_KEY, JSON.stringify(newSession));
      sessionStorage.setItem(SESSION_ID_KEY, newSession.session_id);
    } catch {
      // Ignore storage write errors
    }
  }, []);

  const logout = useCallback(() => {
    setSession(null);
    try {
      sessionStorage.removeItem(STORAGE_KEY);
      sessionStorage.removeItem(SESSION_ID_KEY);
    } catch {
      // Ignore storage remove errors
    }
  }, []);

  // Sync across tabs
  useEffect(() => {
    const handleStorage = (e: StorageEvent) => {
      if (e.key === STORAGE_KEY) {
        if (e.newValue) {
          try {
            setSession(JSON.parse(e.newValue));
          } catch {
            setSession(null);
          }
        } else {
          setSession(null);
        }
      }
    };
    window.addEventListener("storage", handleStorage);
    return () => window.removeEventListener("storage", handleStorage);
  }, []);

  return {
    session,
    isAuthenticated: session !== null,
    isLoading,
    login,
    logout,
  };
}
