import type { Risk } from "../types";

export default function ScorePanel({ risk }: { risk: Risk }) {
  return (
    <details className="card group p-5" data-testid="score-panel">
      <summary className="cursor-pointer list-none text-sm font-semibold text-brand">
        <span className="mr-1 inline-block transition group-open:rotate-90">▸</span> How this score is calculated
      </summary>
      <ul className="mt-3 list-disc space-y-1 pl-5 text-sm text-ink-2">
        {risk.formula.map((l) => <li key={l}>{l}</li>)}
      </ul>
      <p className="mt-3 rounded-xl bg-surface-2 p-3 text-sm"><strong>What it is not:</strong> {risk.disclaimer}</p>
      <p className="mt-2 text-xs text-ink-3">This commit: {risk.scored_methods} scored methods, sum of points {risk.sum_points.toFixed(2)}.</p>
    </details>
  );
}
