import { Bar, BarChart, CartesianGrid, Cell, ErrorBar, Legend, ReferenceLine, ResponsiveContainer, Scatter, ScatterChart, Tooltip, XAxis, YAxis } from "recharts";
import type { Findings, Triple } from "../types";

const BLUE = "#2a78d6", ORANGE = "#eb6834", AQUA = "#1baf7a", INK2 = "#52514e";
const err = (t: Triple) => [t[0] - t[1], t[2] - t[0]];
const fmt = (v: number) => v.toFixed(3);

export function RunsChart({ data }: { data: Findings["runs"] }) {
  const rows = data.rows.map((r, i) => ({ ...r, label: `${r.smell} · ${r.length}× ${r.answer ? "yes" : "no"}`, range: [r.first_ann_id, r.last_ann_id], i }));
  return (
    <ResponsiveContainer width="100%" height={Math.max(260, rows.length * 24)}>
      <BarChart data={rows} layout="vertical" margin={{ left: 20, right: 20 }}>
        <CartesianGrid horizontal={false} stroke="#e4e3df" />
        <XAxis type="number" dataKey="last_ann_id" domain={[0, "dataMax"]} tickFormatter={(v) => `${v}`} label={{ value: "annotation id", position: "insideBottom", offset: -2, fontSize: 12 }} />
        <YAxis type="category" dataKey="label" width={120} tick={{ fontSize: 11 }} />
        <Tooltip formatter={(_: unknown, __: unknown, p: { payload?: { first_ann_id: number; last_ann_id: number; length: number } }) =>
          p.payload ? [`ids ${p.payload.first_ann_id}–${p.payload.last_ann_id} (${p.payload.length} answers)`, "run"] : ""} />
        <Bar dataKey="range" isAnimationActive={false}>
          {rows.map((r) => <Cell key={r.i} fill={r.answer ? ORANGE : BLUE} />)}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

function DotCI({ series, height, xLabel, reference, domain }: {
  series: { name: string; colour: string; shape: "circle" | "triangle" | "square" | "diamond"; points: { y: string; v: Triple }[] }[];
  height: number; xLabel: string; reference?: number; domain?: [number | string, number | string];
}) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <ScatterChart margin={{ left: 20, right: 20, top: 10, bottom: 20 }}>
        <CartesianGrid stroke="#e4e3df" />
        <XAxis type="number" dataKey="x" domain={domain ?? ["auto", "auto"]} tickFormatter={(v: number) => v.toFixed(2)} label={{ value: xLabel, position: "insideBottom", offset: -10, fontSize: 12 }} />
        <YAxis type="category" dataKey="y" width={170} tick={{ fontSize: 11 }} allowDuplicatedCategory={false} />
        <Tooltip formatter={(v: number) => fmt(v)} />
        {reference !== undefined && <ReferenceLine x={reference} stroke={INK2} strokeDasharray="4 4" />}
        <Legend verticalAlign="top" height={30} />
        {series.map((s) => (
          <Scatter key={s.name} name={s.name} data={s.points.map((p) => ({ y: p.y, x: p.v[0], e: err(p.v) }))} fill={s.colour} shape={s.shape}>
            <ErrorBar dataKey="e" direction="x" stroke={s.colour} width={0} strokeWidth={2} />
          </Scatter>
        ))}
      </ScatterChart>
    </ResponsiveContainer>
  );
}

export function CeilingChart({ data }: { data: Findings["ceiling"] }) {
  const y = (r: Findings["ceiling"]["rows"][number]) => `${r.population} (${r.model})`;
  return <DotCI height={280} xLabel="MCC against a single annotation (95% CI)" domain={[-0.2, 1]} reference={0}
    series={[
      { name: "human–human, same snippet", colour: ORANGE, shape: "circle", points: data.rows.map((r) => ({ y: y(r), v: r.human })) },
      { name: "human–human, identical copies", colour: AQUA, shape: "triangle", points: data.rows.map((r) => ({ y: y(r), v: r.copies })) },
      { name: "best model vs one human", colour: BLUE, shape: "square", points: data.rows.map((r) => ({ y: y(r), v: r.model_mcc })) },
    ]} />;
}

export function SpecChart({ data, spec }: { data: Findings["spec"]; spec: string }) {
  const rows = data.rows.filter((r) => r.spec === spec).sort((a, b) => a.smell.localeCompare(b.smell) || a.estimate - b.estimate);
  const toPt = (r: (typeof rows)[number]) => ({ y: `${r.smell} · ${r.condition}`, v: [r.estimate, r.lo, r.hi] as Triple });
  return <DotCI height={Math.max(240, rows.length * 26)} xLabel={`${data.labels[spec]} (95% CI)`} reference={rows[0]?.reference}
    series={[
      { name: "primary analysis", colour: ORANGE, shape: "diamond", points: rows.filter((r) => r.condition.startsWith("primary")).map(toPt) },
      { name: "robustness check", colour: BLUE, shape: "circle", points: rows.filter((r) => !r.condition.startsWith("primary")).map(toPt) },
    ]} />;
}

export function AblationChart({ data }: { data: Findings["ablation"] }) {
  const pops = Array.from(new Set(data.rows.map((r) => `${r.population} (${r.model})`)));
  const colours = [BLUE, ORANGE];
  return <DotCI height={300} xLabel="Change in MCC vs the full DACOS-trained model (95% CI)" reference={0}
    series={pops.map((p, i) => ({ name: p, colour: colours[i % 2], shape: "circle" as const,
      points: data.rows.filter((r) => `${r.population} (${r.model})` === p).map((r) => ({ y: r.variant, v: r.delta_mcc })) }))} />;
}
