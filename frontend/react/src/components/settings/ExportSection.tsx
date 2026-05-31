import { useState } from "react";
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
 * CSV filenames use the app name SanchaySaathi (not SpendSense).
 */
export function ExportSection() {
  const { selMonth } = useMonth();

  const [loadingMonth, setLoadingMonth] = useState(false);
  const [loadingAll,   setLoadingAll]   = useState(false);

  const download = async (
    url:        string,
    filename:   string,
    setLoading: (v: boolean) => void
  ) => {
    setLoading(true);
    try {
      const { data } = await api.get(url, { responseType: "blob" });
      const href = URL.createObjectURL(data);
      const a    = document.createElement("a");
      a.href     = href;
      a.download = filename;
      a.click();
      URL.revokeObjectURL(href);
    } finally {
      setLoading(false);
    }
  };

  const today = new Date().toISOString().slice(0, 10);

  const btnCls =
    "flex-1 flex items-center justify-center gap-2 bg-dark-card2 border border-white/10 " +
    "hover:bg-white/5 py-3 rounded-xl text-sm disabled:opacity-50 transition-colors";

  return (
    <section>
      {/* Section header */}
      <div className="mb-4">
        <h2 className="font-syne font-bold text-white">📥 My Data</h2>
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
              `sanchaySaathi_${selMonth}.csv`,
              setLoadingMonth
            )
          }
          disabled={loadingMonth}
          className={btnCls}
          style={{ color: "var(--text-sub)" }}
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
              `sanchaySaathi_all_${today}.csv`,
              setLoadingAll
            )
          }
          disabled={loadingAll}
          className={btnCls}
          style={{ color: "var(--text-sub)" }}
        >
          {loadingAll
            ? <Loader2 size={14} className="animate-spin" />
            : <Download size={14} />
          }
          Download Full History
        </button>
      </div>
    </section>
  );
}
