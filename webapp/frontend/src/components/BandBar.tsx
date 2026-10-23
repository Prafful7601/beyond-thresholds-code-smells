import type { Band } from "../types";

/** Where a metric value sits relative to the paper's annotated band and the DesigniteJava rule. */
export default function BandBar({ band, value, label }: { band: Band; value: number; label: string }) {
  const max = Math.max(band.hi * 1.6, value * 1.15, band.rule_threshold + 2);
  const pct = (x: number) => `${(100 * Math.min(x, max)) / max}%`;
  return (
    <div className="w-full" aria-label={`${label} = ${value}; band ${band.lo} to ${band.hi}`}>
      <div className="relative h-3 overflow-hidden rounded-full bg-clean/20">
        <div className="absolute inset-y-0 bg-borderline/35" style={{ left: pct(band.lo), width: `calc(${pct(band.hi)} - ${pct(band.lo)})` }} />
        <div className="absolute inset-y-0 right-0 bg-clear/25" style={{ left: pct(band.hi) }} />
        <div className="absolute inset-y-0 w-px bg-ink-2" style={{ left: pct(band.rule_threshold) }} title={`DesigniteJava rule ≥ ${band.rule_threshold}`} />
      </div>
      <div className="relative h-5">
        <div className="absolute -top-4 h-5 w-3 -translate-x-1/2 rounded-full border-2 border-white bg-brand shadow" style={{ left: pct(value) }} />
        <span className="absolute top-1 -translate-x-1/2 whitespace-nowrap text-xs font-semibold" style={{ left: pct(value) }}>{label} = {value}</span>
      </div>
      <div className="flex justify-between text-[11px] text-ink-3"><span>clean</span><span>borderline {band.lo}–{band.hi}</span><span>clear</span></div>
    </div>
  );
}
