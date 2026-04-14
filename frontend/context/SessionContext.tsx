"use client";

import { createContext, useContext, useState, useEffect, useCallback, useMemo, type ReactNode } from "react";
import type { UploadResponse } from "@/types";
import { clearKernCache } from "@/lib/hooks";

export interface BusinessProfile {
  business_name: string;
  industry: string;
  goals: string;
}

const DEFAULT_PROFILE: BusinessProfile = { business_name: "", industry: "", goals: "" };

interface SessionContextValue {
  sessionId: string | null;
  setSessionId: (id: string) => void;
  uploadMeta: UploadResponse | null;
  setUploadMeta: (meta: UploadResponse) => void;
  clearSession: () => void;
  businessProfile: BusinessProfile;
  setBusinessProfile: (profile: BusinessProfile) => void;
  daysStale: number | null;
}

const SessionContext = createContext<SessionContextValue | null>(null);

export function SessionProvider({ children }: { children: ReactNode }) {
  const [sessionId, setSessionIdState] = useState<string | null>(null);
  const [uploadMeta, setUploadMeta] = useState<UploadResponse | null>(null);
  const [businessProfile, setBusinessProfileState] = useState<BusinessProfile>(DEFAULT_PROFILE);
  const [hydrated, setHydrated] = useState(false);

  useEffect(() => {
    const stored = sessionStorage.getItem("kern_session_id");
    if (stored) setSessionIdState(stored);
    const storedMeta = sessionStorage.getItem("kern_upload_meta");
    if (storedMeta) {
      try { setUploadMeta(JSON.parse(storedMeta)); } catch { /* ignore */ }
    }
    const storedProfile = localStorage.getItem("kern_business_profile");
    if (storedProfile) {
      try { setBusinessProfileState(JSON.parse(storedProfile)); } catch { /* ignore */ }
    }
    setHydrated(true);
  }, []);

  const setSessionId = useCallback((id: string) => {
    setSessionIdState(id);
    sessionStorage.setItem("kern_session_id", id);
    clearKernCache();
  }, []);

  const setUploadMetaWrapped = useCallback((meta: UploadResponse) => {
    setUploadMeta(meta);
    sessionStorage.setItem("kern_upload_meta", JSON.stringify(meta));
  }, []);

  const setBusinessProfile = useCallback((profile: BusinessProfile) => {
    setBusinessProfileState(profile);
    localStorage.setItem("kern_business_profile", JSON.stringify(profile));
  }, []);

  const clearSession = useCallback(() => {
    setSessionIdState(null);
    setUploadMeta(null);
    sessionStorage.removeItem("kern_session_id");
    sessionStorage.removeItem("kern_upload_meta");
  }, []);

  const daysStale = useMemo(() => {
    if (!uploadMeta?.date_range?.max) return null;
    const maxDate = new Date(uploadMeta.date_range.max);
    if (isNaN(maxDate.getTime())) return null;
    const now = new Date();
    const diffMs = now.getTime() - maxDate.getTime();
    return Math.floor(diffMs / (1000 * 60 * 60 * 24));
  }, [uploadMeta]);

  if (!hydrated) return null;

  return (
    <SessionContext.Provider
      value={{
        sessionId,
        setSessionId,
        uploadMeta,
        setUploadMeta: setUploadMetaWrapped,
        clearSession,
        businessProfile,
        setBusinessProfile,
        daysStale,
      }}
    >
      {children}
    </SessionContext.Provider>
  );
}

export function useSession() {
  const ctx = useContext(SessionContext);
  if (!ctx) throw new Error("useSession must be used within SessionProvider");
  return ctx;
}
