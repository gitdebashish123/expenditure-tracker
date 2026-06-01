import { createContext, useContext, useState, useCallback, useRef } from "react";

/**
 * ToastContext — lightweight in-app notification system
 *
 * Streamlit ref: replaces st.toast() throughout the app.
 * Toasts auto-dismiss after 3 seconds.
 * Stack of up to N toasts, newest on top.
 *
 * Position:
 *   Mobile:  bottom-centre, above the bottom nav bar (bottom-20)
 *   Desktop: bottom-right (bottom-4, right-4)
 *
 * Usage:
 *   const { toast } = useToast();
 *   toast("Expense saved", { icon: "⚡" });
 *   toast("Something went wrong", { type: "error" });
 *   toast("Info message", { type: "info" });
 */

export type ToastType = "success" | "error" | "info" | "warning";

interface Toast {
  id:      number;
  message: string;
  type:    ToastType;
  icon?:   string;
}

interface ToastContextValue {
  toast: (message: string, opts?: { type?: ToastType; icon?: string }) => void;
}

const ToastContext = createContext<ToastContextValue>({} as ToastContextValue);

const TYPE_CLASSES: Record<ToastType, string> = {
  success: "bg-emerald-500/15 border-emerald-500/30 text-emerald-300",
  error:   "bg-red-500/15 border-red-500/30 text-red-300",
  info:    "bg-indigo-500/15 border-indigo-500/30 text-indigo-300",
  warning: "bg-amber-500/15 border-amber-500/30 text-amber-300",
};

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);
  const nextId = useRef(0);

  const toast = useCallback(
    (message: string, opts?: { type?: ToastType; icon?: string }) => {
      const id = ++nextId.current;
      setToasts(prev => [...prev, {
        id,
        message,
        type: opts?.type ?? "success",
        icon: opts?.icon,
      }]);
      // Auto-dismiss after 3 seconds
      setTimeout(() => {
        setToasts(prev => prev.filter(t => t.id !== id));
      }, 3000);
    },
    []
  );

  return (
    <ToastContext.Provider value={{ toast }}>
      {children}

      {/* Toast stack */}
      {toasts.length > 0 && (
        <div
          className="fixed z-50 flex flex-col gap-2 w-72
                     bottom-20 left-1/2 -translate-x-1/2
                     sm:bottom-4 sm:left-auto sm:right-4 sm:translate-x-0"
        >
          {toasts.map(t => (
            <div
              key={t.id}
              className={`flex items-center gap-2 px-4 py-3 rounded-xl border
                          text-sm animate-slide-up shadow-lg
                          ${TYPE_CLASSES[t.type]}`}
            >
              {t.icon && <span className="flex-shrink-0">{t.icon}</span>}
              <span>{t.message}</span>
            </div>
          ))}
        </div>
      )}
    </ToastContext.Provider>
  );
}

export const useToast = () => useContext(ToastContext);
