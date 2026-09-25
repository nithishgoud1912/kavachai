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


export function useSession(): SessionState {
  const [session, setSession] = useState<Session | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let active = true;
    async function initSession() {
      try {
        const verified = await getCurrentSession();
        if (!active) return;
        setSession(verified);
        sessionStorage.setItem(STORAGE_KEY, JSON.stringify({name:verified.name,department:verified.department,issued_at:verified.issued_at,expires_at:verified.expires_at,roles:verified.roles}));
      } catch {
        if (!active) return;
        sessionStorage.removeItem(STORAGE_KEY);
        setSession(null);
      } finally { if (active) setIsLoading(false); }
    }
    void initSession();
    return () => { active = false; };
  }, []);

  const login = useCallback((newSession: Session) => {
    setSession(newSession);
    try {
      sessionStorage.setItem(STORAGE_KEY, JSON.stringify({name:newSession.name,department:newSession.department,issued_at:newSession.issued_at,expires_at:newSession.expires_at,roles:newSession.roles}));

    } catch {
      // Ignore storage write errors
    }
  }, []);

  const logout = useCallback(() => {
    revokeSession().catch(() => {});

    setSession(null);
    try {
      sessionStorage.removeItem(STORAGE_KEY);
    } catch {
      // Ignore storage remove errors
    }
  }, []);

  // Recheck cross-tab session changes with the HttpOnly cookie.
  useEffect(() => {
    const handleStorage = (event: StorageEvent) => {
      if (event.key === STORAGE_KEY && event.newValue === null) setSession(null);
      if (event.key === STORAGE_KEY && event.newValue !== null) {
        getCurrentSession().then(setSession).catch(() => setSession(null));
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
