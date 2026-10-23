import { useEffect, useState } from "react";
import { Link, useLocation, useParams } from "react-router-dom";
import { api } from "../api";
import MethodDrawer from "../components/MethodDrawer";
import MethodsTable from "../components/MethodsTable";
import RiskGauge from "../components/RiskGauge";
import ScorePanel from "../components/ScorePanel";
import type { Analysis, MethodResult } from "../types";
import { useConfig } from "../useConfig";

const STAGES = ["queued", "fetching commit", "fetching files", "parsing methods", "scoring", "done"];
const REPO_STAGES = ["queued", "fetching commit", "downloading repository", "parsing methods", "scoring", "done"];

export function Progress({ stage, mode }: { stage: string; mode?: string }) {
  const stages = mode === "repo" ? REPO_STAGES : STAGES;
  const at = Math.max(0, stages.indexOf(stage));
  return (
    <div className="card mx-auto max-w-xl p-6" data-testid="progress">
      <p className="font-semibold">Analysing…</p>
      <ol className="mt-4 space-y-2">
        {stages.slice(1, -1).map((s, i) => {
          const done = at > i + 1, now = at === i + 1;
          return <li key={s} className="flex items-center gap-3 text-sm">
            <span className={`flex h-5 w-5 items-center justify-center rounded-full text-[10px] font-bold ${done ? "bg-clean text-white" : now ? "animate-pulse bg-brand text-white" : "bg-surface-3 text-ink-3"}`}>{done ? "✓" : i + 1}</span>
            <span className={now ? "font-semibold" : done ? "text-ink-2" : "text-ink-3"}>{s[0].toUpperCase() + s.slice(1)}</span></li>;
        })}
      </ol>
    </div>
  );
}

function Stat({ label, value, tone }: { label: string; value: number | string; tone?: string }) {
  return <div className="card p-4"><p className="text-xs font-semibold uppercase tracking-wide text-ink-3">{label}</p>
    <p className={`mt-1 text-2xl font-extrabold tabular-nums ${tone ?? ""}`}>{value}</p></div>;
}

export default function Results() {
  const { id = "" } = useParams();
  const { config } = useConfig();
  const handed = (useLocation().state as { analysis?: Analysis } | null)?.analysis;
  const [a, setA] = useState<Analysis | null>(handed?.id === id ? handed : null);
  const [error, setError] = useState<string | null>(null);
  const [open, setOpen] = useState<MethodResult | null>(null);

  useEffect(() => {
    if (handed?.id === id && handed.status !== "running") { setA(handed); return; }
    let stop = false;
    let timer: ReturnType<typeof setTimeout>;
    const poll = async () => {
      try {
        const r = await api.analysis(id);
        if (stop) return;
        setA(r);
        if (r.status === "running") timer = setTimeout(poll, 800);
      } catch (e) { if (!stop) setError((e as Error).message); }
    };
    void poll();
    return () => { stop = true; clearTimeout(timer); };
  }, [id, handed]);

  if (error) return <ErrorBox message={error} />;
  if (!a || a.status === "running") return <Progress stage={a?.stage ?? "queued"} mode={(a?.request?.mode as string) ?? "commit"} />;
  if (a.status === "error") return <ErrorBox message={a.error ?? "The analysis failed."} />;
  const r = a.result!;
  const s = r.summary;
  const p = r.risk.params;
  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="min-w-0">
          <p className="text-sm text-ink-3">{r.target.kind}{r.cached ? " · cached" : ""} · analysed in {r.duration_s}s</p>
          <h1 className="mt-1 text-2xl font-extrabold tracking-tight">{r.repo}</h1>
          <p className="mt-1 max-w-3xl truncate text-ink-2">{r.target.title}</p>
          <p className="mt-1 font-mono text-xs text-ink-3">{r.target.sha}{r.target.base_sha ? ` (compared with ${r.target.base_sha.slice(0, 12)})` : ""}</p>
        </div>
        <div className="flex flex-wrap gap-2">
          {r.target.url && <a className="btn-ghost" href={r.target.url} target="_blank" rel="noreferrer">View on GitHub ↗</a>}
          {(["json", "csv", "pdf"] as const).map((k) => <a key={k} className="btn-ghost" href={api.reportUrl(a.id, k)} download>{k.toUpperCase()}</a>)}
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-[minmax(0,320px)_1fr]">
        <div className="card flex flex-col items-center justify-center p-6">
          <p className="mb-2 text-sm font-semibold text-ink-2">Smell risk score</p>
          <RiskGauge score={r.risk.score} band={r.risk.band} mediumFrom={p.medium_from} highAbove={p.high_above} />
          {r.risk.small_sample && <p className="mt-3 rounded-lg bg-borderline/10 px-3 py-2 text-center text-xs text-borderline" data-testid="small-sample">
            Small sample: fewer than {p.small_sample_below} changed methods, so the score is unstable.</p>}
          <p className="mt-3 text-center text-xs text-ink-3">{r.risk.disclaimer}</p>
        </div>
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-5">
            <Stat label="Changed methods" value={s.changed_methods} />
            <Stat label="Introduced" value={s.introduced} tone="text-clear" />
            <Stat label="Worsened" value={s.worsened} tone="text-borderline" />
            <Stat label="Improved" value={s.improved} tone="text-clean" />
            <Stat label="Clean" value={s.clean} />
          </div>
          <div className="grid grid-cols-3 gap-3 text-sm">
            <div className="rounded-xl bg-clear/5 p-3"><span className="font-bold text-clear">{s.clear}</span> clear (above band)</div>
            <div className="rounded-xl bg-borderline/5 p-3"><span className="font-bold text-borderline">{s.borderline}</span> borderline: candidates, not verdicts</div>
            <div className="rounded-xl bg-surface-2 p-3"><span className="font-bold">{s.deleted}</span> deleted (not scored)</div>
          </div>
          <ScorePanel risk={r.risk} />
          {r.warnings.map((w) => <p key={w} className="rounded-xl bg-surface-2 p-3 text-xs text-ink-2">⚠ {w}</p>)}
        </div>
      </div>

      {r.methods.length ? <MethodsTable methods={r.methods} onSelect={setOpen} />
        : <div className="card p-8 text-center text-ink-2">This change touches no Java methods, so there is nothing to score.</div>}
      {open && <MethodDrawer method={open} config={config} onClose={() => setOpen(null)} />}
    </div>
  );
}

export function ErrorBox({ message }: { message: string }) {
  return <div className="card mx-auto max-w-xl p-6 text-center" role="alert">
    <p className="text-lg font-bold">Something went wrong</p>
    <p className="mt-2 text-sm text-ink-2">{message}</p>
    <Link to="/" className="btn-primary mt-4">Try another commit</Link></div>;
}
