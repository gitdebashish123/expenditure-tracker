import { useEffect, useRef } from "react";

interface InactivityTimerOptions {
  enabled:    boolean;
  warningMs:  number;   // ms before timeout to show the warning (e.g. 4 * 60 * 1000)
  timeoutMs:  number;   // ms of inactivity before onTimeout fires (e.g. 5 * 60 * 1000)
  onWarn:     () => void;
  onTimeout:  () => void;
}

/**
 * useInactivityTimer — logs out the user after a period of inactivity.
 *
 * Resets on: mousemove, keydown, touchstart, scroll.
 * At warningMs: calls onWarn() (show toast).
 * At timeoutMs: calls onTimeout() (call logout()).
 * Only active when enabled=true (i.e. user is logged in).
 */
export function useInactivityTimer({
  enabled,
  warningMs,
  timeoutMs,
  onWarn,
  onTimeout,
}: InactivityTimerOptions) {
  const warnTimer    = useRef<ReturnType<typeof setTimeout> | null>(null);
  const logoutTimer  = useRef<ReturnType<typeof setTimeout> | null>(null);
  // Stable refs so the event listeners don't become stale closures
  const onWarnRef    = useRef(onWarn);
  const onTimeoutRef = useRef(onTimeout);

  useEffect(() => { onWarnRef.current = onWarn; },    [onWarn]);
  useEffect(() => { onTimeoutRef.current = onTimeout; }, [onTimeout]);

  useEffect(() => {
    if (!enabled) return;

    const clear = () => {
      if (warnTimer.current)   clearTimeout(warnTimer.current);
      if (logoutTimer.current) clearTimeout(logoutTimer.current);
    };

    const reset = () => {
      clear();
      warnTimer.current   = setTimeout(() => onWarnRef.current(),    warningMs);
      logoutTimer.current = setTimeout(() => onTimeoutRef.current(), timeoutMs);
    };

    const EVENTS = ["mousemove", "keydown", "touchstart", "scroll"] as const;
    EVENTS.forEach(e => window.addEventListener(e, reset, { passive: true }));
    reset(); // start the timers immediately on mount

    return () => {
      clear();
      EVENTS.forEach(e => window.removeEventListener(e, reset));
    };
  }, [enabled, warningMs, timeoutMs]);
}
