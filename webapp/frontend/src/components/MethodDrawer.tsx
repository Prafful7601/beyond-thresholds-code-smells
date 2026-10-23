import { useEffect } from "react";
import type { MethodResult, SiteConfig, Smell } from "../types";
import BandBar from "./BandBar";
import { StatusChip, ZoneChip } from "./Chips";

export default function MethodDrawer({ method, config, onClose }: { method: MethodResult; config: SiteConfig | null; onClose: () => void }) {
  useEffect(() => {
    const h = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    window.addEventListener("keydown", h);
    return () => window.removeEventListener("keydown", h);
  }, [onClose]);
  const changed = new Set(method.changed_lines);
  const lines = method.code.split("\n");
  const side = method.after ?? method.before;
  return (
    <div className="fixed inset-0 z-50 flex justify-end" role="dialog" aria-modal="true" aria-label={`Method ${method.name}`}>
      <div className="absolute inset-0 bg-ink/30" onClick={onClose} />
      <aside className="relative flex h-full w-full max-w-3xl flex-col overflow-y-auto bg-white shadow-2xl" data-testid="method-drawer">
        <div className="sticky top-0 z-10 flex items-start justify-between gap-3 border-b border-surface-3 bg-white p-5">
          <div className="min-w-0">
            <h3 className="font-mono text-lg font-bold">{method.name}</h3>
            <p className="truncate font-mono text-xs text-ink-3">{method.file} · lines {method.start_line}–{method.end_line} · {method.change_type}{method.has_body ? "" : " · declaration without body"}</p>
          </div>
          <div className="flex items-center gap-2"><StatusChip status={method.status} /><button className="btn-ghost px-3 py-1" onClick={onClose} aria-label="Close">✕</button></div>
        </div>
        <div className="space-y-6 p-5">
          <section>
            <h4 className="mb-2 text-sm font-semibold text-ink-2">Code {method.change_type !== "scanned" && <span className="font-normal text-ink-3">(changed lines highlighted)</span>}</h4>
            <pre className="max-h-80 overflow-auto rounded-xl bg-[#0f172a] py-3 text-xs leading-5 text-slate-100" data-testid="code">
              {lines.map((l, i) => {
                const n = method.start_line + i;
                return <div key={i} className={changed.has(n) ? "bg-amber-400/25" : ""}>
                  <span className="inline-block w-12 select-none pr-3 text-right text-slate-500">{n}</span>{l || " "}</div>;
              })}
            </pre>
          </section>
          {(["CM", "LPL"] as Smell[]).map((s) => {
            const sm = method.smells[s];
            const cfg = config?.smells[s];
            const metric = s === "CM" ? "cc" : "pc";
            return (
              <section key={s} className="rounded-2xl border border-surface-3 p-4">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <h4 className="font-semibold">{cfg?.name ?? s}</h4>
                  <div className="flex items-center gap-2"><ZoneChip zone={sm.zone} /><StatusChip status={sm.status} /></div>
                </div>
                {cfg && side && <div className="mt-6"><BandBar band={cfg.band} value={side[metric]} label={metric} /></div>}
                {method.before && method.after && <p className="mt-1 text-xs text-ink-3">Before: {metric} = {method.before[metric]} ({method.before[s].zone}, P = {method.before[s].probability.toFixed(2)}) → after: {metric} = {method.after[metric]}</p>}
                <dl className="mt-3 grid grid-cols-2 gap-3 text-sm">
                  <div className="rounded-xl bg-surface-2 p-3"><dt className="text-xs text-ink-3">DesigniteJava default rule</dt>
                    <dd className="font-semibold">{sm.rule ? "flags it" : "does not flag it"}{cfg ? <span className="font-normal text-ink-3"> ({metric} ≥ {cfg.band.rule_threshold})</span> : null}</dd></div>
                  <div className="rounded-xl bg-surface-2 p-3"><dt className="text-xs text-ink-3">Model probability {cfg ? `(${cfg.model.model})` : ""}</dt>
                    <dd className="font-semibold">{sm.probability.toFixed(2)}{sm.zone !== "borderline" && <span className="font-normal text-ink-3"> · extrapolation outside the band</span>}</dd></div>
                </dl>
                <p className={`mt-3 rounded-xl p-3 text-sm ${sm.zone === "borderline" ? "border border-borderline/30 bg-borderline/5" : "bg-surface-2 text-ink-2"}`} data-testid={`note-${s}`}>{sm.note}</p>
              </section>
            );
          })}
          {side && <details className="text-sm"><summary className="cursor-pointer font-semibold text-brand">All metrics</summary>
            <table className="mt-2 text-xs"><tbody>
              {(["cc", "cc_lizard", "pc", "loc", "statements", "max_nesting", "method_calls", "comment_ratio", "mean_identifier_length"] as const).map((k) => (
                <tr key={k}><td className="pr-6 font-mono text-ink-2">{k}</td><td className="tabular-nums">{method.before ? `${method.before[k]} → ` : ""}{method.after ? method.after[k] : "–"}</td></tr>))}
            </tbody></table></details>}
        </div>
      </aside>
    </div>
  );
}
