import { useMemo, useState } from "react";
import type { MethodResult, Smell } from "../types";
import { StatusChip, ZoneChip } from "./Chips";

type SortKey = "file" | "name" | "change_type" | "cc" | "pc" | "pCM" | "pLPL" | "status" | "points";
const STATUS_ORDER: Record<string, number> = { introduced: 0, worsened: 1, improved: 2, unchanged: 3, "n/a": 3, removed: 4 };

function val(m: MethodResult, k: SortKey): string | number {
  const side = m.after ?? m.before;
  switch (k) {
    case "cc": return side?.cc ?? 0;
    case "pc": return side?.pc ?? 0;
    case "pCM": return m.smells.CM.probability;
    case "pLPL": return m.smells.LPL.probability;
    case "status": return STATUS_ORDER[m.status] ?? 9;
    case "points": return m.points ?? -1;
    default: return String(m[k]);
  }
}
const arrow = (m: MethodResult, k: "cc" | "pc") =>
  m.change_type === "scanned" ? `${m.after?.[k]}` : `${m.before ? m.before[k] : "–"} → ${m.after ? m.after[k] : "–"}`;

export default function MethodsTable({ methods, onSelect }: { methods: MethodResult[]; onSelect: (m: MethodResult) => void }) {
  const [sort, setSort] = useState<{ key: SortKey; desc: boolean }>({ key: "status", desc: false });
  const [status, setStatus] = useState("all");
  const [zone, setZone] = useState("all");
  const [q, setQ] = useState("");
  const rows = useMemo(() => {
    const f = methods.filter((m) => (status === "all" || m.status === status)
      && (zone === "all" || (["CM", "LPL"] as Smell[]).some((s) => m.smells[s].zone === zone))
      && (!q || `${m.file} ${m.name}`.toLowerCase().includes(q.toLowerCase())));
    return [...f].sort((a, b) => {
      const x = val(a, sort.key), y = val(b, sort.key);
      const c = x < y ? -1 : x > y ? 1 : 0;
      return sort.desc ? -c : c;
    });
  }, [methods, sort, status, zone, q]);
  const th = (k: SortKey, label: string) => (
    <th scope="col" className="cursor-pointer select-none whitespace-nowrap px-3 py-2 text-left font-semibold hover:text-brand"
        onClick={() => setSort((s) => ({ key: k, desc: s.key === k ? !s.desc : false }))}
        aria-sort={sort.key === k ? (sort.desc ? "descending" : "ascending") : "none"}>
      {label}{sort.key === k ? (sort.desc ? " ↓" : " ↑") : ""}
    </th>
  );
  const statuses = Array.from(new Set(methods.map((m) => m.status)));
  return (
    <div className="card overflow-hidden">
      <div className="flex flex-wrap items-center gap-2 border-b border-surface-3 p-3">
        <input className="input max-w-xs py-2" placeholder="Filter by file or method" value={q} onChange={(e) => setQ(e.target.value)} aria-label="Filter by file or method" />
        <select className="input w-auto py-2" value={status} onChange={(e) => setStatus(e.target.value)} aria-label="Status filter">
          <option value="all">All statuses</option>{statuses.map((s) => <option key={s} value={s}>{s}</option>)}
        </select>
        <select className="input w-auto py-2" value={zone} onChange={(e) => setZone(e.target.value)} aria-label="Zone filter">
          <option value="all">All zones</option><option value="clear">clear</option><option value="borderline">borderline</option><option value="clean">clean</option>
        </select>
        <span className="ml-auto text-xs text-ink-3">{rows.length} of {methods.length} methods · click a row for details</span>
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-full text-sm" data-testid="methods-table">
          <thead className="bg-surface-2 text-xs uppercase tracking-wide text-ink-2">
            <tr>{th("file", "File")}{th("name", "Method")}{th("change_type", "Change")}{th("cc", "cc")}{th("pc", "pc")}
              <th className="px-3 py-2 text-left font-semibold">Complex Method</th><th className="px-3 py-2 text-left font-semibold">Long Param. List</th>
              {th("pCM", "P(CM)")}{th("pLPL", "P(LPL)")}{th("status", "Status")}{th("points", "Points")}</tr>
          </thead>
          <tbody>
            {rows.map((m) => (
              <tr key={`${m.file}:${m.start_line}:${m.name}`} onClick={() => onSelect(m)} tabIndex={0}
                  onKeyDown={(e) => { if (e.key === "Enter") onSelect(m); }}
                  className="cursor-pointer border-t border-surface-3 hover:bg-brand-light/50 focus:bg-brand-light/50 focus:outline-none">
                <td className="max-w-[16rem] truncate px-3 py-2 font-mono text-xs text-ink-2" title={m.file}>{m.file}:{m.start_line}</td>
                <td className="px-3 py-2 font-mono text-xs font-semibold">{m.name}</td>
                <td className="px-3 py-2 text-ink-2">{m.change_type}</td>
                <td className="whitespace-nowrap px-3 py-2 tabular-nums">{arrow(m, "cc")}</td>
                <td className="whitespace-nowrap px-3 py-2 tabular-nums">{arrow(m, "pc")}</td>
                {(["CM", "LPL"] as Smell[]).map((s) => (
                  <td key={s} className="whitespace-nowrap px-3 py-2"><ZoneChip zone={m.smells[s].zone} />
                    <span className="ml-1 text-xs text-ink-3" title="DesigniteJava default rule">{m.smells[s].rule ? "rule: yes" : "rule: no"}</span></td>
                ))}
                <td className="px-3 py-2 tabular-nums">{m.smells.CM.probability.toFixed(2)}</td>
                <td className="px-3 py-2 tabular-nums">{m.smells.LPL.probability.toFixed(2)}</td>
                <td className="px-3 py-2"><StatusChip status={m.status} /></td>
                <td className="px-3 py-2 tabular-nums">{m.points === null ? "–" : m.points.toFixed(2)}</td>
              </tr>
            ))}
            {!rows.length && <tr><td colSpan={11} className="px-3 py-8 text-center text-ink-3">No methods match the filters.</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  );
}
