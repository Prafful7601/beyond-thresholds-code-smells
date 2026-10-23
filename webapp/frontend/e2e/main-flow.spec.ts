import { expect, test } from "@playwright/test";
import { readFileSync } from "node:fs";

const load = (name: string) => JSON.parse(readFileSync(new URL(`./fixtures/${name}.json`, import.meta.url), "utf-8"));
const analysis = load("analysis");
const config = load("config");
const findings = load("findings");

test("analyse a commit: progress, score, table, drawer, history and research pages", async ({ page }) => {
  let polls = 0;
  await page.route("http://api.test/**", async (route) => {
    const url = new URL(route.request().url());
    const json = (body: unknown, status = 200) => route.fulfill({ status, contentType: "application/json", body: JSON.stringify(body) });
    if (url.pathname === "/config") return json(config);
    if (url.pathname === "/findings") return json(findings);
    if (url.pathname === "/history") return json([{ ...analysis, result: null }]);
    if (url.pathname === "/analyze") {
      const body = route.request().postDataJSON();
      expect(body.repo_url).toBe("https://github.com/o/r");
      return json({ id: analysis.id, status: "running" }, 202);
    }
    if (url.pathname === `/analysis/${analysis.id}`) {
      polls += 1;
      return json(polls < 4 ? { ...analysis, status: "running", stage: "parsing methods", result: null } : analysis);
    }
    return json({ detail: "not mocked" }, 404);
  });

  await page.goto("/");
  await expect(page.getByRole("heading", { name: "How smelly is this commit?" })).toBeVisible();
  await expect(page.getByTestId("project-card")).toContainText("SDG 9");
  await page.getByLabel("GitHub repository, commit or pull-request URL").fill("https://github.com/o/r");
  await page.getByLabel("Commit SHA").fill("a".repeat(40));
  await page.getByRole("button", { name: "Analyze" }).click();

  await expect(page.getByTestId("progress")).toBeVisible();
  await expect(page.getByTestId("risk-score")).toHaveText(new RegExp(analysis.result.risk.score.toFixed(1)));
  await expect(page.getByTestId("small-sample")).toBeVisible();
  await expect(page.getByText("not a probability of bugs").first()).toBeVisible();
  const rows = page.getByTestId("methods-table").locator("tbody tr");
  await expect(rows).toHaveCount(analysis.result.methods.length);

  await page.getByText("How this score is calculated").click();
  await expect(page.getByTestId("score-panel")).toContainText(config.risk.formula[0]);

  await rows.filter({ hasText: "tax" }).click();
  await expect(page.getByTestId("method-drawer")).toBeVisible();
  await expect(page.getByTestId("note-LPL")).toContainText("Candidate to review, not a verdict");
  await page.keyboard.press("Escape");
  await expect(page.getByTestId("method-drawer")).toBeHidden();

  await page.getByRole("link", { name: "History" }).click();
  await expect(page.getByRole("link", { name: "o/r" })).toBeVisible();
  await page.getByRole("link", { name: "Research findings" }).click();
  await expect(page.getByText(findings.ceiling.caption)).toBeVisible();
});

test("friendly error when the API rejects the input", async ({ page }) => {
  await page.route("http://api.test/**", (route) => {
    const p = new URL(route.request().url()).pathname;
    if (p === "/config") return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(config) });
    return route.fulfill({ status: 400, contentType: "application/json", body: JSON.stringify({ detail: "That is not a GitHub URL." }) });
  });
  await page.goto("/");
  await page.getByLabel("GitHub repository, commit or pull-request URL").fill("https://gitlab.com/x/y");
  await page.getByRole("button", { name: "Analyze" }).click();
  await expect(page.getByRole("alert")).toContainText("That is not a GitHub URL.");
});
