import { PROJECT } from "../project";
import { useConfig } from "../useConfig";

export default function About() {
  const { config } = useConfig();
  return (
    <article className="prose-sm mx-auto max-w-3xl space-y-6">
      <h1 className="text-2xl font-extrabold tracking-tight">About CodeSniff</h1>
      <section className="card space-y-2 p-5"><h2 className="font-bold">What it does</h2>
        <p className="text-sm text-ink-2">For a commit or pull request it finds the Java methods that changed, computes the paper's metrics before and after, places each method in a
          zone for Complex Method (cyclomatic complexity) and Long Parameter List (parameter count), shows the DesigniteJava default rule's verdict and the
          probability from the paper's best model, and combines them into a transparent 0–100 smell risk score.</p></section>
      <section className="card space-y-2 p-5"><h2 className="font-bold">What it does not claim</h2>
        <ul className="list-disc space-y-1 pl-5 text-sm text-ink-2">
          <li>A borderline method is a <strong>candidate to review, not a verdict</strong>: in that band human annotators disagree and the best models are weak.</li>
          <li>{config?.risk.disclaimer ?? "The score measures code-smell risk, not bugs or build failures."}</li>
          <li>Outside the annotated band the model probability is an extrapolation.</li>
          <li>Metrics are lizard-based approximations of the paper's DesigniteJava metrics; agreement rates are in the model card.</li>
          {config && Object.entries(config.excluded).map(([k, v]) => <li key={k}><strong>{k}:</strong> {v}</li>)}
        </ul></section>
      {config && <section className="card space-y-2 p-5"><h2 className="font-bold">Models</h2>
        <ul className="list-disc space-y-1 pl-5 text-sm text-ink-2">
          {(["CM", "LPL"] as const).map((s) => { const m = config.smells[s].model; return (
            <li key={s}>{config.smells[s].name}: {m.model} trained on {m.training_data.n} unanimous DACOS entities ({m.training_data.smelly} smelly / {m.training_data.benign} benign).
              Paper cross-validated MCC {m.paper_cv.MCC.toFixed(3)} [95% CI {m.paper_cv.MCC_lo.toFixed(3)}, {m.paper_cv.MCC_hi.toFixed(3)}]; trained {m.trained_at} at commit <code>{m.repository_commit.slice(0, 7)}</code>.</li>); })}
        </ul></section>}
      <section className="card space-y-2 p-5"><h2 className="font-bold">Data</h2>
        <p className="text-sm text-ink-2">DACOS: H. Nandani, M. Saad, T. Sharma, <em>DACOS—A Manually Annotated Dataset of Code Smells</em>, MSR 2023. Dataset doi:10.5281/zenodo.7570428 (CC BY 4.0).
          CodeSniff ships only trained models and result tables, not DACOS data.</p></section>
      <section className="card space-y-2 p-5"><h2 className="font-bold">Limitations</h2>
        <ul className="list-disc space-y-1 pl-5 text-sm text-ink-2">
          <li>Java only; methods are found with lizard plus a fallback for interface and abstract declarations.</li>
          <li>Changed methods are matched across versions by name (and parameter count for overloads); renamed methods count as deleted + added.</li>
          <li>GitHub lists at most 300 files per commit; very large commits are capped.</li>
          <li>The labels behind the models come from a dataset with documented quality issues (see the paper).</li>
        </ul></section>
      <section className="card space-y-1 p-5"><h2 className="font-bold">Team</h2>
        {PROJECT.team.map((m) => <p key={m.roll} className="text-sm">{m.name} <span className="font-mono text-xs text-ink-3">{m.roll}</span></p>)}
        <p className="pt-2 text-sm">Supervisor: {PROJECT.supervisor} · Co-supervisor: {PROJECT.coSupervisor}</p>
        <p className="text-sm text-ink-2">{PROJECT.meta} · {PROJECT.institute}</p></section>
    </article>
  );
}
