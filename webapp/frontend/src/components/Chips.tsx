import type { Status, Zone } from "../types";

const ZONE: Record<Zone, string> = {
  clean: "bg-clean/10 text-clean ring-1 ring-clean/30",
  borderline: "bg-borderline/10 text-borderline ring-1 ring-borderline/30",
  clear: "bg-clear/10 text-clear ring-1 ring-clear/30",
};
const ZONE_TEXT: Record<Zone, string> = { clean: "clean", borderline: "borderline", clear: "clear" };
const STATUS: Record<string, string> = {
  introduced: "bg-clear/10 text-clear", worsened: "bg-borderline/10 text-borderline", improved: "bg-clean/10 text-clean",
  unchanged: "bg-surface-2 text-ink-2", removed: "bg-surface-2 text-ink-3", "n/a": "bg-surface-2 text-ink-3",
};

export function ZoneChip({ zone }: { zone: Zone }) {
  return <span className={`chip ${ZONE[zone]}`} title={zone === "borderline" ? "Candidate to review, not a verdict" : undefined}>{ZONE_TEXT[zone]}</span>;
}
export function StatusChip({ status }: { status: Status }) {
  return <span className={`chip ${STATUS[status] ?? STATUS.unchanged}`}>{status}</span>;
}
export const BAND_COLOUR: Record<string, string> = { Low: "#1baf7a", Medium: "#eb6834", High: "#c0392b", "n/a": "#8a8984" };
