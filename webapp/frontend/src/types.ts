export type Zone = "clean" | "borderline" | "clear";
export type Smell = "CM" | "LPL";
export type Status = "introduced" | "worsened" | "improved" | "unchanged" | "removed" | "n/a";

export interface SmellResult { zone: Zone; rule: boolean; probability: number; note: string; status: Status; }
export interface Side {
  cc: number; cc_lizard: number; pc: number; loc: number; statements: number; max_nesting: number;
  method_calls: number; comment_ratio: number; mean_identifier_length: number; start_line: number; end_line: number;
  CM: Omit<SmellResult, "status">; LPL: Omit<SmellResult, "status">;
}
export interface MethodResult {
  file: string; name: string; change_type: "added" | "modified" | "deleted" | "scanned";
  start_line: number; end_line: number; changed_lines: number[]; code: string; has_body: boolean;
  before: Side | null; after: Side | null; smells: Record<Smell, SmellResult>; points: number | null; status: Status;
}
export interface Risk {
  score: number | null; band: "Low" | "Medium" | "High" | "n/a"; scored_methods: number; sum_points: number;
  small_sample: boolean; params: Record<string, number>; formula: string[]; disclaimer: string;
}
export interface Summary {
  changed_methods: number; added: number; modified: number; deleted: number; introduced: number; worsened: number;
  improved: number; clean: number; borderline: number; clear: number;
}
export interface AnalysisResult {
  repo: string; repo_url: string; mode: string; target: { kind: string; sha: string; base_sha?: string | null; title?: string; url?: string; author?: string; date?: string; number?: number };
  risk: Risk; summary: Summary; methods: MethodResult[]; warnings: string[]; java_files: number; duration_s: number; cached?: boolean;
}
export interface Analysis {
  id: string; status: "running" | "done" | "error"; stage: string; created_at: string; finished_at?: string;
  repo?: string; sha?: string; mode?: string; score?: number | null; band?: string; error?: string | null;
  request: Record<string, unknown>; result: AnalysisResult | null;
}
export interface Band { metric: string; lo: number; hi: number; rule_threshold: number; }
export interface Evidence { estimate: number; ci_lo: number; ci_hi: number; label: string; source_table: string; }
export interface SiteConfig {
  risk: { params: Record<string, number>; formula: string[]; disclaimer: string };
  smells: Record<Smell, { name: string; metric: string; band: Band; anomalous_values: Record<string, { entities: number; share_smelly: number }>;
    evidence: Record<"model" | "same" | "copies", Evidence>;
    model: { model: string; features: string[]; hyperparameters: Record<string, unknown>; trained_at: string; repository_commit: string;
             training_data: { source: string; set: string; n: number; smelly: number; benign: number; projects: number };
             paper_cv: { MCC: number; MCC_lo: number; MCC_hi: number; source: string }; probability: string } }>;
  excluded: Record<string, string>;
  links: { repository: string; results: string; paper: string };
}
export type Triple = [number, number, number];
export interface Findings {
  runs: { rows: { smell: string; first_ann_id: number; last_ann_id: number; length: number; answer: number }[]; caption: string };
  ceiling: { rows: { population: string; model: string; human: Triple; copies: Triple; model_mcc: Triple }[]; caption: string };
  spec: { rows: { spec: string; smell: string; condition: string; estimate: number; lo: number; hi: number; reference: number }[];
          labels: Record<string, string>; caption: string };
  ablation: { rows: { population: string; model: string; variant: string; delta_mcc: Triple }[]; caption: string };
  links: { repository: string; results: string; paper: string };
}
