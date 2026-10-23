import { BAND_COLOUR } from "./Chips";

/** Semicircle gauge 0-100 with the Low / Medium / High bands taken from the backend's risk parameters. */
export default function RiskGauge({ score, band, mediumFrom, highAbove }: { score: number | null; band: string; mediumFrom: number; highAbove: number }) {
  const r = 80, cx = 100, cy = 95;
  const pt = (v: number) => { const a = Math.PI * (1 - v / 100); return [cx + r * Math.cos(a), cy - r * Math.sin(a)]; };
  const arc = (a: number, b: number) => { const [x1, y1] = pt(a); const [x2, y2] = pt(b); return `M ${x1} ${y1} A ${r} ${r} 0 0 1 ${x2} ${y2}`; };
  const v = score ?? 0;
  const [nx, ny] = pt(Math.max(0, Math.min(100, v)));
  return (
    <figure className="flex flex-col items-center" aria-label={`Smell risk score ${score === null ? "not available" : score.toFixed(1)} of 100, ${band}`}>
      <svg viewBox="0 0 200 110" className="w-60 max-w-full">
        <path d={arc(0, mediumFrom)} stroke={BAND_COLOUR.Low} strokeWidth="16" fill="none" opacity="0.85" />
        <path d={arc(mediumFrom, highAbove)} stroke={BAND_COLOUR.Medium} strokeWidth="16" fill="none" opacity="0.85" />
        <path d={arc(highAbove, 100)} stroke={BAND_COLOUR.High} strokeWidth="16" fill="none" opacity="0.85" />
        {score !== null && <><line x1={cx} y1={cy} x2={nx} y2={ny} stroke="#0b0b0b" strokeWidth="3" strokeLinecap="round" />
          <circle cx={cx} cy={cy} r="5" fill="#0b0b0b" /></>}
      </svg>
      <div className="-mt-2 text-center">
        <div className="text-4xl font-extrabold tabular-nums" data-testid="risk-score">{score === null ? "–" : score.toFixed(1)}<span className="text-lg font-semibold text-ink-3"> / 100</span></div>
        <div className="mt-1 text-sm font-bold" style={{ color: BAND_COLOUR[band] }} data-testid="risk-band">{band === "n/a" ? "no changed methods" : `${band} smell risk`}</div>
      </div>
    </figure>
  );
}
