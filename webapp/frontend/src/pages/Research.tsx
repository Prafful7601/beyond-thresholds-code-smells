import { useEffect, useState } from "react";
import { api } from "../api";
import { AblationChart, CeilingChart, RunsChart, SpecChart } from "../components/Charts";
import type { Findings } from "../types";

function Block({ title, caption, children }: { title: string; caption: string; children: React.ReactNode }) {
  return <section className="card p-5"><h2 className="text-lg font-bold">{title}</h2><p className="mt-1 text-sm text-ink-2">{caption}</p>
    <div className="mt-4">{children}</div></section>;
}

export default function Research() {
  const [f, setF] = useState<Findings | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [spec, setSpec] = useState("alpha");
  useEffect(() => { api.findings().then(setF).catch((e: Error) => setError(e.message)); }, []);
  if (error) return <p className="text-sm text-clear" role="alert">{error}</p>;
  if (!f) return <p className="text-sm text-ink-3">Loading the paper's results…</p>;
  return (
    <div className="space-y-6">
      <div><h1 className="text-2xl font-extrabold tracking-tight">Research findings</h1>
        <p className="mt-1 max-w-3xl text-ink-2">The evidence behind CodeSniff, from <em>{f.links.paper}</em>. Every value is read from the paper's result tables.
          {" "}<a className="text-brand hover:underline" href={f.links.results} target="_blank" rel="noreferrer">Full results</a> ·{" "}
          <a className="text-brand hover:underline" href={f.links.repository} target="_blank" rel="noreferrer">repository</a></p></div>
      <Block title="1. Long runs of identical answers in DACOS" caption={f.runs.caption}><RunsChart data={f.runs} /></Block>
      <Block title="2. How far models are from human agreement" caption={f.ceiling.caption}><CeilingChart data={f.ceiling} /></Block>
      <Block title="3. Do the headline numbers survive other readings of the data?" caption={f.spec.caption}>
        <select className="input mb-3 w-auto py-2" value={spec} onChange={(e) => setSpec(e.target.value)} aria-label="Headline">
          {Object.entries(f.spec.labels).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
        </select>
        <SpecChart data={f.spec} spec={spec} /></Block>
      <Block title="4. What the models learn from (ablation)" caption={f.ablation.caption}><AblationChart data={f.ablation} /></Block>
    </div>
  );
}
