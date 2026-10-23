import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import { BAND_COLOUR } from "../components/Chips";
import type { Analysis } from "../types";

export default function History() {
  const [rows, setRows] = useState<Analysis[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => { api.history().then(setRows).catch((e: Error) => setError(e.message)); }, []);
  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-extrabold tracking-tight">History</h1>
      {error && <p className="text-sm text-clear" role="alert">{error}</p>}
      {!rows && !error && <p className="text-sm text-ink-3">Loading…</p>}
      {rows && !rows.length && <p className="card p-6 text-sm text-ink-2">No analyses yet. <Link className="text-brand" to="/">Analyse a commit</Link>.</p>}
      {rows && rows.length > 0 && (
        <div className="card overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead className="bg-surface-2 text-left text-xs uppercase tracking-wide text-ink-2"><tr>
              <th className="px-4 py-2">Date (UTC)</th><th className="px-4 py-2">Repository</th><th className="px-4 py-2">Commit</th><th className="px-4 py-2">Mode</th><th className="px-4 py-2">Score</th><th className="px-4 py-2">Status</th></tr></thead>
            <tbody>
              {rows.map((h) => (
                <tr key={h.id} className="border-t border-surface-3 hover:bg-brand-light/40">
                  <td className="px-4 py-2 tabular-nums text-ink-2"><Link to={`/analysis/${h.id}`} className="hover:text-brand">{h.created_at.replace("T", " ").slice(0, 16)}</Link></td>
                  <td className="px-4 py-2 font-semibold"><Link to={`/analysis/${h.id}`}>{h.repo ?? String(h.request.repo_url ?? h.request.pr_url ?? "")}</Link></td>
                  <td className="px-4 py-2 font-mono text-xs">{h.sha?.slice(0, 12) ?? "–"}</td>
                  <td className="px-4 py-2 text-ink-2">{h.mode ?? String(h.request.mode)}</td>
                  <td className="px-4 py-2 font-bold tabular-nums" style={{ color: BAND_COLOUR[h.band ?? "n/a"] }}>{h.score == null ? "–" : `${h.score.toFixed(1)} ${h.band}`}</td>
                  <td className="px-4 py-2 text-ink-2">{h.status === "error" ? <span className="text-clear" title={h.error ?? ""}>error</span> : h.status}</td>
                </tr>))}
            </tbody>
          </table>
        </div>)}
    </div>
  );
}
