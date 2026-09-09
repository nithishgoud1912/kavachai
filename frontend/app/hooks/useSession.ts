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

import { getCurrentSession, revokeSession } from "@/app/services/api";

const STORAGE_KEY = "kavachai_session";
const SESSION_ID_KEY = "kavachai_session_id";

export function useSession(): SessionState {
  const [session, setSession] = useState<Session | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function initSession() {
      try {
        const stored = sessionStorage.getItem(STORAGE_KEY);
        if (stored) {
          const parsed = JSON.parse(stored);
          setSession(parsed);

          // Verify with server in background
          try {
            const verified = await getCurrentSession();
            setSession(verified);
            sessionStorage.setItem(STORAGE_KEY, JSON.stringify(verified));
          } catch {
            // Session expired or revoked on server
            sessionStorage.removeItem(STORAGE_KEY);
            sessionStorage.removeItem(SESSION_ID_KEY);
            setSession(null);
          }
        }
      } catch {
        // Ignore parsing errors
      } finally {
        setIsLoading(false);
      }
    }

    initSession();
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
    const currentId = session?.session_id || (typeof window !== "undefined" ? sessionStorage.getItem(SESSION_ID_KEY) : null);
    if (currentId) {
      revokeSession(currentId).catch(() => {});
    }

    setSession(null);
    try {
      sessionStorage.removeItem(STORAGE_KEY);
      sessionStorage.removeItem(SESSION_ID_KEY);
    } catch {
      // Ignore storage remove errors
    }
  }, [session]);

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
