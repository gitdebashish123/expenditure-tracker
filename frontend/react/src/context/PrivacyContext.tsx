import { createContext, useContext, useState, useCallback, useEffect } from "react";

const STORAGE_KEY = "walletmantra_privacy_mode";

interface PrivacyContextValue {
  valuesHidden: boolean;
  togglePrivacy: () => void;
}

const PrivacyContext = createContext<PrivacyContextValue | null>(null);

export function PrivacyProvider({ children }: { children: React.ReactNode }) {
  const [valuesHidden, setValuesHidden] = useState(false);

  // Clear any previously stored "hidden" state so no one is stranded
  useEffect(() => {
    try { localStorage.removeItem(STORAGE_KEY); } catch { /* ignore */ }
  }, []);

  const togglePrivacy = useCallback(() => {
    setValuesHidden(prev => !prev);
  }, []);

  return (
    <PrivacyContext.Provider value={{ valuesHidden, togglePrivacy }}>
      {children}
    </PrivacyContext.Provider>
  );
}

export function usePrivacy(): PrivacyContextValue {
  const ctx = useContext(PrivacyContext);
  if (!ctx) throw new Error("usePrivacy must be used inside PrivacyProvider");
  return ctx;
}
