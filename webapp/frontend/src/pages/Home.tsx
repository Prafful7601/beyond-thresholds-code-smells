import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, parseInput } from "../api";
import { EXAMPLES } from "../project";
import { useConfig } from "../useConfig";

export default function Home() {
  const nav = useNavigate();
  const { config } = useConfig();
  const [text, setText] = useState("");
  const [sha, setSha] = useState("");
  const [mode, setMode] = useState<"commit" | "repo">("commit");
  const [maxFiles, setMaxFiles] = useState(300);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(e?: FormEvent, override?: string) {
    e?.preventDefault();
    const input = (override ?? text).trim();
    if (!input) { setError("Enter a GitHub repository, commit or pull-request URL."); return; }
    setBusy(true); setError(null);
    try {
      const { id } = await api.analyze(parseInput(input, override ? "" : sha, mode, maxFiles));
      nav(`/analysis/${id}`);
    } catch (err) { setError((err as Error).message); setBusy(false); }
  }

  const p = config?.risk.params;
  return (
    <div className="space-y-10">
      <section className="mx-auto max-w-3xl pt-6 text-center">
        <p className="chip bg-brand-light px-3 py-1 text-brand">Java · Complex Method · Long Parameter List</p>
        <h1 className="mt-4 text-4xl font-extrabold tracking-tight sm:text-5xl">How smelly is this commit?</h1>
        <p className="mx-auto mt-4 max-w-2xl text-ink-2">CodeSniff scores the code-smell risk of the Java methods a commit changes, and tells you honestly where
          that judgement is uncertain. Borderline results are <strong>candidates to review, not verdicts</strong>.</p>
      </section>

      <form onSubmit={submit} className="card mx-auto max-w-3xl space-y-4 p-5 sm:p-6" data-testid="analyze-form">
        <label className="block text-sm font-semibold" htmlFor="target">GitHub repository, commit or pull-request URL</label>
        <input id="target" className="input text-base" placeholder="https://github.com/owner/repo/commit/… or …/pull/123 or https://github.com/owner/repo"
               value={text} onChange={(e) => setText(e.target.value)} autoFocus />
        <div className="grid gap-3 sm:grid-cols-[1fr_auto]">
          <input className="input" placeholder="Commit SHA (optional; default: latest commit on the default branch)" value={sha}
                 onChange={(e) => setSha(e.target.value)} aria-label="Commit SHA" disabled={/\/pull\/|\/commit\//.test(text)} />
          <div className="flex rounded-xl border border-surface-3 bg-surface-2 p-1 text-sm" role="radiogroup" aria-label="Mode">
            {(["commit", "repo"] as const).map((m) => (
              <button type="button" key={m} role="radio" aria-checked={mode === m} onClick={() => setMode(m)}
                      className={`rounded-lg px-3 py-1.5 font-medium ${mode === m ? "bg-white shadow text-brand" : "text-ink-2"}`}>
                {m === "commit" ? "Changed code" : "Scan whole repo"}</button>))}
          </div>
        </div>
        {mode === "repo" && (
          <label className="flex items-center gap-3 text-sm text-ink-2">Maximum Java files
            <input type="number" min={10} max={2000} step={10} value={maxFiles} onChange={(e) => setMaxFiles(Number(e.target.value))} className="input w-28 py-2" /></label>)}
        {error && <p className="rounded-xl border border-clear/30 bg-clear/5 p-3 text-sm text-clear" role="alert">{error}</p>}
        <div className="flex flex-wrap items-center gap-3">
          <button className="btn-primary px-6 py-3 text-base" disabled={busy}>{busy ? "Starting…" : "Analyze"}</button>
          <span className="text-xs text-ink-3">Public repositories work without a token; the server can use GITHUB_TOKEN for private ones.</span>
        </div>
        <div className="border-t border-surface-3 pt-4">
          <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-ink-3">Try an example</p>
          <div className="flex flex-wrap gap-2">
            {EXAMPLES.map((ex) => (
              <button type="button" key={ex.input} className="btn-ghost" disabled={busy}
                      onClick={() => { setText(ex.input); setMode("commit"); void submit(undefined, ex.input); }}>{ex.label}</button>))}
          </div>
        </div>
      </form>

      <section className="grid gap-4 sm:grid-cols-3">
        {config ? (["clean", "borderline", "clear"] as const).map((z) => {
          const cm = config.smells.CM.band, lpl = config.smells.LPL.band;
          const text = z === "clean" ? `below the band humans judged (cc < ${cm.lo}, pc < ${lpl.lo})`
            : z === "borderline" ? `inside it (cc ${cm.lo}–${cm.hi}, pc ${lpl.lo}–${lpl.hi}): humans disagree, models are weak`
            : `above it (cc > ${cm.hi}, pc > ${lpl.hi}): clearly smelly by threshold`;
          return <div key={z} className="card p-5"><p className={`text-sm font-bold text-${z}`}>{z}</p><p className="mt-1 text-sm text-ink-2">{text}</p></div>;
        }) : <div className="card col-span-3 p-5 text-sm text-ink-3">Loading the paper's bands…</div>}
      </section>
      {p && <p className="mx-auto max-w-3xl text-center text-sm text-ink-3">The commit's smell risk score (0–100) averages per-method points: {p.clear_points} for a clear smell,
        {" "}{p.borderline_weight} × model probability for a borderline one, +{p.change_bonus} for each introduced or worsened smell. {config?.risk.disclaimer}</p>}
    </div>
  );
}
