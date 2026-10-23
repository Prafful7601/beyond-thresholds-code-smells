import type { MethodResult, Risk, SiteConfig } from "../types";

const side = (cc: number, pc: number, zoneCM: "clean" | "borderline" | "clear", zoneLPL: "clean" | "borderline" | "clear", p = 0.5) => ({
  cc, cc_lizard: cc, pc, loc: 10, statements: 5, max_nesting: 1, method_calls: 2, comment_ratio: 0, mean_identifier_length: 6,
  start_line: 10, end_line: 14,
  CM: { zone: zoneCM, rule: cc >= 8, probability: p, note: zoneCM === "borderline" ? "Candidate to review, not a verdict. CM note." : "Below the band. extrapolation" },
  LPL: { zone: zoneLPL, rule: pc >= 5, probability: p, note: zoneLPL === "borderline" ? "Candidate to review, not a verdict. LPL note." : "Below the band. extrapolation" },
});

export const METHODS: MethodResult[] = [
  { file: "src/A.java", name: "alpha", change_type: "modified", start_line: 10, end_line: 14, changed_lines: [11, 12],
    code: "int alpha(int a) {\n  if (a > 1) { return 1; }\n  return 0;\n  // end\n}", has_body: true,
    before: side(2, 1, "clean", "clean", 0.3), after: side(6, 1, "borderline", "clean", 0.6),
    smells: { CM: { ...side(6, 1, "borderline", "clean", 0.6).CM, status: "introduced" }, LPL: { ...side(6, 1, "borderline", "clean").LPL, status: "unchanged" } },
    points: 0.55, status: "introduced" },
  { file: "src/B.java", name: "beta", change_type: "added", start_line: 3, end_line: 5, changed_lines: [3, 4, 5],
    code: "void beta() {\n}\n", has_body: true, before: null, after: side(1, 0, "clean", "clean", 0.2),
    smells: { CM: { ...side(1, 0, "clean", "clean", 0.2).CM, status: "unchanged" }, LPL: { ...side(1, 0, "clean", "clean", 0.2).LPL, status: "unchanged" } },
    points: 0, status: "unchanged" },
  { file: "src/C.java", name: "gamma", change_type: "deleted", start_line: 1, end_line: 2, changed_lines: [],
    code: "void gamma() {}", has_body: true, before: side(1, 0, "clean", "clean"), after: null,
    smells: { CM: { ...side(1, 0, "clean", "clean").CM, status: "removed" }, LPL: { ...side(1, 0, "clean", "clean").LPL, status: "removed" } },
    points: null, status: "removed" },
];

export const RISK: Risk = {
  score: 27.5, band: "Medium", scored_methods: 2, sum_points: 0.55, small_sample: true,
  params: { clear_points: 1, borderline_weight: 0.5, change_bonus: 0.25, method_cap: 1, probability_delta: 0.2, small_sample_below: 3, medium_from: 25, high_above: 50 },
  formula: ["method points = 1 if any smell is clear", "score = 100 × (sum of method points) / (number of changed methods)"],
  disclaimer: "It is not a probability of bugs, defects or build failure.",
};

const band = { metric: "cc", lo: 5, hi: 14, rule_threshold: 8 };
export const CONFIG = {
  risk: { params: RISK.params, formula: RISK.formula, disclaimer: RISK.disclaimer },
  smells: {
    CM: { name: "Complex Method", metric: "cc", band, anomalous_values: {}, evidence: {} as never,
          model: { model: "LR", features: [], hyperparameters: {}, trained_at: "2026-10-23", repository_commit: "abcdef0123", training_data: { source: "", set: "", n: 1695, smelly: 1129, benign: 566, projects: 10 }, paper_cv: { MCC: 0.1, MCC_lo: 0.05, MCC_hi: 0.15, source: "" }, probability: "" } },
    LPL: { name: "Long Parameter List", metric: "pc", band: { metric: "pc", lo: 3, hi: 10, rule_threshold: 5 }, anomalous_values: {}, evidence: {} as never,
          model: { model: "SVM", features: [], hyperparameters: {}, trained_at: "2026-10-23", repository_commit: "abcdef0123", training_data: { source: "", set: "", n: 1189, smelly: 731, benign: 458, projects: 10 }, paper_cv: { MCC: 0.27, MCC_lo: 0.2, MCC_hi: 0.3, source: "" }, probability: "" } },
  },
  excluded: { MA: "descriptive only" },
  links: { repository: "https://github.com/x/y", results: "https://github.com/x/y/results", paper: "Paper" },
} as unknown as SiteConfig;
