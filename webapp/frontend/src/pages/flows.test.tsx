import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import App from "../App";
import { _resetConfigCache } from "../useConfig";
// Real backend output, shared with the Playwright test.
import ANALYSIS from "../../e2e/fixtures/analysis.json";
import CONFIG from "../../e2e/fixtures/config.json";
import FINDINGS from "../../e2e/fixtures/findings.json";

type Handler = (path: string, init?: RequestInit) => { status?: number; body: unknown } | undefined;

function mockApi(extra?: Handler) {
  const calls: { path: string; body?: unknown }[] = [];
  vi.stubGlobal("fetch", vi.fn(async (url: string, init?: RequestInit) => {
    const path = new URL(url).pathname;
    calls.push({ path, body: init?.body ? JSON.parse(String(init.body)) : undefined });
    const r = extra?.(path, init) ?? (
      path === "/config" ? { body: CONFIG }
      : path === "/findings" ? { body: FINDINGS }
      : path === "/history" ? { body: [{ ...ANALYSIS, result: null }] }
      : path.startsWith("/analysis/") ? { body: ANALYSIS }
      : path === "/analyze" ? { status: 202, body: { id: ANALYSIS.id, status: "running" } }
      : { status: 404, body: { detail: "not found" } });
    return new Response(JSON.stringify(r.body), { status: r.status ?? 200 });
  }));
  return calls;
}

const at = (path: string) => render(<MemoryRouter initialEntries={[path]}><App /></MemoryRouter>);

beforeEach(() => _resetConfigCache());
afterEach(() => vi.unstubAllGlobals());

it("Home shows the paper's bands and submits a commit URL", async () => {
  const calls = mockApi();
  at("/");
  await waitFor(() => expect(screen.getByText(/inside it \(cc 5–14, pc 3–10\)/)).toBeInTheDocument());
  await userEvent.type(screen.getByLabelText("GitHub repository, commit or pull-request URL"), "https://github.com/o/r");
  await userEvent.type(screen.getByLabelText("Commit SHA"), "abc1234");
  await userEvent.click(screen.getByRole("button", { name: "Analyze" }));
  await waitFor(() => expect(screen.getByTestId("risk-score")).toBeInTheDocument());
  expect(calls.find((c) => c.path === "/analyze")?.body).toEqual({ repo_url: "https://github.com/o/r", commit_sha: "abc1234", mode: "commit" });
});

it("Home validates empty input and shows API errors", async () => {
  mockApi((p) => (p === "/analyze" ? { status: 400, body: { detail: "That is not a GitHub URL." } } : undefined));
  at("/");
  await userEvent.click(screen.getByRole("button", { name: "Analyze" }));
  expect(screen.getByRole("alert")).toHaveTextContent("Enter a GitHub repository");
  await userEvent.type(screen.getByLabelText("GitHub repository, commit or pull-request URL"), "https://gitlab.com/x/y");
  await userEvent.click(screen.getByRole("button", { name: "Analyze" }));
  await waitFor(() => expect(screen.getByRole("alert")).toHaveTextContent("That is not a GitHub URL."));
});

it("Home repo mode sends the file cap", async () => {
  const calls = mockApi();
  at("/");
  await userEvent.click(screen.getByRole("radio", { name: "Scan whole repo" }));
  fireEvent.change(screen.getByLabelText(/Maximum Java files/), { target: { value: "50" } });
  await userEvent.type(screen.getByLabelText("GitHub repository, commit or pull-request URL"), "https://github.com/o/r");
  await userEvent.click(screen.getByRole("button", { name: "Analyze" }));
  await waitFor(() => expect(calls.some((c) => c.path === "/analyze")).toBe(true));
  expect(calls.find((c) => c.path === "/analyze")?.body).toMatchObject({ mode: "repo", max_files: 50 });
});

it("Results shows score, counts, downloads, table and drawer", async () => {
  mockApi();
  at(`/analysis/${ANALYSIS.id}`);
  const score = await screen.findByTestId("risk-score");
  expect(score).toHaveTextContent(ANALYSIS.result.risk.score.toFixed(1));
  expect(screen.getByTestId("small-sample")).toBeInTheDocument();
  expect(screen.getAllByText(/not a probability of bugs/i).length).toBeGreaterThan(0);
  for (const k of ["JSON", "CSV", "PDF"]) {
    expect(screen.getByRole("link", { name: k })).toHaveAttribute("href", expect.stringContaining(`/analysis/${ANALYSIS.id}/report.${k.toLowerCase()}`));
  }
  const rows = within(screen.getByTestId("methods-table")).getAllByRole("row");
  expect(rows.length).toBe(ANALYSIS.result.methods.length + 1);
  await userEvent.click(rows[1]);
  expect(await screen.findByTestId("method-drawer")).toBeInTheDocument();
});

it("Results shows progress while running and the error message on failure", async () => {
  mockApi((p) => (p.startsWith("/analysis/") ? { body: { ...ANALYSIS, status: "running", stage: "fetching files", result: null } } : undefined));
  const view = at("/analysis/x1");
  expect(await screen.findByTestId("progress")).toHaveTextContent("Fetching files");
  view.unmount();
  mockApi((p) => (p.startsWith("/analysis/") ? { body: { ...ANALYSIS, status: "error", error: "GitHub API rate limit reached", result: null } } : undefined));
  at("/analysis/x2");
  expect(await screen.findByRole("alert")).toHaveTextContent("GitHub API rate limit reached");
});

it("Results reports an unreachable API", async () => {
  vi.stubGlobal("fetch", vi.fn(async () => { throw new TypeError("network"); }));
  at("/analysis/x3");
  expect(await screen.findByRole("alert")).toHaveTextContent("Cannot reach the CodeSniff API");
});

it("History lists past analyses with their score", async () => {
  mockApi();
  at("/history");
  const table = await screen.findByRole("table");
  expect(table).toHaveTextContent(ANALYSIS.repo);
  expect(table).toHaveTextContent(`${ANALYSIS.score.toFixed(1)} ${ANALYSIS.band}`);
});

it("History shows an empty state", async () => {
  mockApi((p) => (p === "/history" ? { body: [] } : undefined));
  at("/history");
  expect(await screen.findByText(/No analyses yet/)).toBeInTheDocument();
});

it("Research renders all four findings with captions from the API", async () => {
  mockApi();
  at("/research");
  expect(await screen.findByText("1. Long runs of identical answers in DACOS")).toBeInTheDocument();
  for (const c of [FINDINGS.runs.caption, FINDINGS.ceiling.caption, FINDINGS.ablation.caption]) expect(screen.getByText(c)).toBeInTheDocument();
  await userEvent.selectOptions(screen.getByLabelText("Headline"), "auc");
  expect(screen.getByLabelText("Headline")).toHaveValue("auc");
});

it("Unknown routes show not found inside the layout with the project card", async () => {
  mockApi();
  at("/nope");
  expect(screen.getByText("Page not found.")).toBeInTheDocument();
  expect(screen.getByTestId("project-card")).toBeInTheDocument();
});
