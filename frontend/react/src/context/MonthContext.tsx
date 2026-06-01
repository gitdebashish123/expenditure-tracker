import { createContext, useContext, useEffect, useState } from "react";

// Read the current month at call time (not module load time)
const getCurrentMonth = () => new Date().toISOString().slice(0, 7);

interface MonthContextValue {
  selMonth:    string;
  setSelMonth: (m: string) => void;
  isCurrent:   boolean;
}

const MonthContext = createContext<MonthContextValue>({} as MonthContextValue);

export function MonthProvider({ children }: { children: React.ReactNode }) {
  const [selMonth,     setSelMonth]     = useState(getCurrentMonth);
  const [currentMonth, setCurrentMonth] = useState(getCurrentMonth);

  // Re-check on tab focus — catches the "open app next morning" case where the
  // static constant would stay on the previous day's month until a full reload.
  useEffect(() => {
    const handler = () => {
      const now = getCurrentMonth();
      if (now !== currentMonth) setCurrentMonth(now);
    };
    document.addEventListener("visibilitychange", handler);
    return () => document.removeEventListener("visibilitychange", handler);
  }, [currentMonth]);

  return (
    <MonthContext.Provider
      value={{
        selMonth,
        setSelMonth,
        isCurrent: selMonth === currentMonth,
      }}
    >
      {children}
    </MonthContext.Provider>
  );
}

export const useMonth = () => useContext(MonthContext);
