import type { Analysis, Findings, SiteConfig } from "./types";

// VITE_API_URL if set; otherwise the same-origin /api path in production builds (Vercel services rewrite /api/* to the
// backend) and the local backend in development.
export const API_URL: string = (import.meta.env.VITE_API_URL as string | undefined)?.replace(/\/$/, "")
  || (import.meta.env.PROD ? "/api" : "http://localhost:8000");

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${API_URL}${path}`, { headers: { "Content-Type": "application/json" }, ...init });
  } catch {
    throw new Error(`Cannot reach the CodeSniff API at ${API_URL}. Is the backend running?`);
  }
  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try { detail = (await res.json()).detail ?? detail; } catch { /* keep default */ }
    throw new Error(detail);
  }
  return res.json() as Promise<T>;
}

export interface AnalyzeInput { repo_url?: string; commit_sha?: string; pr_url?: string; mode: "commit" | "repo"; max_files?: number; }

export const api = {
  // Returns {id, status: "running"} for a background job, or the finished record when the server runs inline (serverless).
  analyze: (body: AnalyzeInput) => request<Pick<Analysis, "id" | "status"> & Partial<Analysis>>("/analyze", { method: "POST", body: JSON.stringify(body) }),
  analysis: (id: string) => request<Analysis>(`/analysis/${id}`),
  history: () => request<Analysis[]>("/history"),
  findings: () => request<Findings>("/findings"),
  config: () => request<SiteConfig>("/config"),
  reportUrl: (id: string, kind: "json" | "csv" | "pdf") => `${API_URL}/analysis/${id}/report.${kind}`,
};

/** Split a single input box into the API's fields. */
export function parseInput(text: string, sha: string, mode: "commit" | "repo", maxFiles?: number): AnalyzeInput {
  const t = text.trim();
  if (/\/pull\/\d+/.test(t)) return { pr_url: t, mode };
  return { repo_url: t, commit_sha: sha.trim() || undefined, mode, max_files: mode === "repo" ? maxFiles : undefined };
}
