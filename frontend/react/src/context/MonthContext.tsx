import { createContext, useContext, useState } from "react";

// Current month in YYYY-MM format
const CURRENT_MONTH = new Date().toISOString().slice(0, 7);

interface MonthContextValue {
  selMonth: string;
  setSelMonth: (m: string) => void;
  isCurrent: boolean;
}

const MonthContext = createContext<MonthContextValue>({} as MonthContextValue);

export function MonthProvider({ children }: { children: React.ReactNode }) {
  const [selMonth, setSelMonth] = useState(CURRENT_MONTH);

  return (
    <MonthContext.Provider
      value={{
        selMonth,
        setSelMonth,
        isCurrent: selMonth === CURRENT_MONTH,
      }}
    >
      {children}
    </MonthContext.Provider>
  );
}

export const useMonth = () => useContext(MonthContext);
