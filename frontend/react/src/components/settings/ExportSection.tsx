import { useState, useEffect } from "react";
import { api } from "@/api/client";
import { useMonth } from "@/context/MonthContext";
import { fmtMonth } from "@/utils/formatDate";
import { Download, Loader2 } from "lucide-react";

/**
 * ExportSection — CSV download buttons
 *
 * Streamlit ref: settings_section("📥", "My Data", ...) in with tab5:
 * Two buttons: current month CSV + full history CSV.
 *
 * Key improvement: loading spinner during download
 * (Streamlit st.download_button had no loading state).
 *
 * Uses blob response type + createObjectURL for programmatic download.
 * CSV filenames use the app name Wallet Mantra.
 */
export function ExportSection() {
  const { selMonth } = useMonth();

  const [loadingMonth, setLoadingMonth] = useState(false);
  const [loadingAll,   setLoadingAll]   = useState(false);
  const [showRange,    setShowRange]    = useState(false);
  const [fromDate,     setFromDate]     = useState(() => `${selMonth}-01`);
  const [toDate,       setToDate]       = useState(() => new Date().toISOString().slice(0, 10));
  const [loadingRange, setLoadingRange] = useState(false);

  useEffect(() => {
    setFromDate(`${selMonth}-01`);
  }, [selMonth]);

  const download = async (
    url:        string,
    filename:   string,
    setLoading: (v: boolean) => void
  ) => {
    setLoading(true);
    try {
      const { data } = await api.get(url, { responseType: "blob" });
      const href = URL.createObjectURL(data);
      const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent);

      if (isIOS) {
        // iOS Safari does not honour the download attribute on blob: URLs.
        // Opening in a new tab lets the user Save to Files via share sheet.
        window.open(href, "_blank");
        // Delay revoke so the new tab has time to read the blob
        setTimeout(() => URL.revokeObjectURL(href), 5000);
      } else {
        const a = document.createElement("a");
        a.href = href;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(href);
      }
    } finally {
      setLoading(false);
    }
  };

  const today = new Date().toISOString().slice(0, 10);

  const fmtD = (iso: string) =>
    new Date(iso + "T00:00:00").toLocaleDateString("en-IN", {
      day: "numeric", month: "short", year: "numeric",
    });

  const btnCls =
    "flex-1 flex items-center justify-center gap-2 bg-dark-card2 border border-white/10 " +
    "hover:bg-white/5 py-3 rounded-xl text-sm text-white disabled:opacity-50 transition-colors";

  return (
    <section>
      {/* Section header */}
      <div className="mb-4">
        <h2 className="font-syne font-bold text-white">📥 Export data</h2>
        <p className="text-sm mt-0.5" style={{ color: "var(--text-sub)" }}>
          Download your expense history as a CSV file.
        </p>
        <div className="border-b border-white/10 mt-3" />
      </div>

      <div className="flex gap-3">
        {/* Current month CSV */}
        <button
          onClick={() =>
            download(
              `/export/csv/${selMonth}`,
              `walletMantra_${selMonth}.csv`,
              setLoadingMonth
            )
          }
          disabled={loadingMonth}
          className={btnCls}
        >
          {loadingMonth
            ? <Loader2 size={14} className="animate-spin" />
            : <Download size={14} />
          }
          Download {fmtMonth(selMonth)}
        </button>

        {/* Full history CSV */}
        <button
          onClick={() =>
            download(
              "/export/csv/all",
              `walletMantra_all_${today}.csv`,
              setLoadingAll
            )
          }
          disabled={loadingAll}
          className={btnCls}
        >
          {loadingAll
            ? <Loader2 size={14} className="animate-spin" />
            : <Download size={14} />
          }
          Download Full History
        </button>
      </div>

      {/* Custom range toggle */}
      <button
        onClick={() => setShowRange(v => !v)}
        className="mt-3 text-xs w-full text-center py-1.5 rounded-lg border transition-colors"
        style={{
          borderColor: showRange ? "var(--accent)"    : "var(--border-lg)",
          color:       showRange ? "var(--accent)"    : "var(--text)",
          background:  showRange ? "var(--accent-bg)" : "transparent",
          fontWeight:  showRange ? 600 : 400,
        }}
      >
        {showRange ? "▲ Hide date range" : "▼ Custom date range"}
      </button>

      {showRange && (
        <div className="mt-3 space-y-3">
          <div className="flex gap-3 items-center">
            <div className="flex-1">
              <label className="text-xs mb-1 block" style={{ color: "var(--text-sub)" }}>From</label>
              <input
                type="date"
                value={fromDate}
                onChange={e => setFromDate(e.target.value)}
                className="w-full bg-dark-card2 border border-white/10 rounded-xl
                           px-3 py-2 text-white text-sm focus:border-accent focus:outline-none"
              />
            </div>
            <div className="flex-1">
              <label className="text-xs mb-1 block" style={{ color: "var(--text-sub)" }}>To</label>
              <input
                type="date"
                value={toDate}
                onChange={e => setToDate(e.target.value)}
                className="w-full bg-dark-card2 border border-white/10 rounded-xl
                           px-3 py-2 text-white text-sm focus:border-accent focus:outline-none"
              />
            </div>
          </div>
          <button
            onClick={() =>
              download(
                `/export/csv/range?from_date=${fromDate}&to_date=${toDate}`,
                `walletMantra_${fromDate}_to_${toDate}.csv`,
                setLoadingRange
              )
            }
            disabled={loadingRange || fromDate > toDate}
            className="w-full flex items-center justify-center gap-2 bg-gradient-to-r
                       from-accent to-accent2 text-white font-semibold py-3 rounded-xl
                       text-sm disabled:opacity-50 transition-opacity"
          >
            {loadingRange ? <Loader2 size={14} className="animate-spin" /> : <Download size={14} />}
            Download {fmtD(fromDate)} → {fmtD(toDate)}
          </button>
          {fromDate > toDate && (
            <p className="text-xs text-red-400 text-center">"From" must be before "To"</p>
          )}
        </div>
      )}

      {/iPad|iPhone|iPod/.test(navigator.userAgent) && (
        <p className="text-xs mt-2 text-center" style={{ color: "var(--text-muted)" }}>
          On iPhone/iPad, the file opens in a new tab — tap Share → Save to Files
        </p>
      )}
    </section>
  );
}
