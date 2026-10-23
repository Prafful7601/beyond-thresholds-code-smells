import { fireEvent, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { parseInput } from "../api";
import { CONFIG, METHODS, RISK } from "../test/fixtures";
import MethodDrawer from "./MethodDrawer";
import MethodsTable from "./MethodsTable";
import RiskGauge from "./RiskGauge";
import ScorePanel from "./ScorePanel";

describe("RiskGauge", () => {
  it("shows the score and band", () => {
    render(<RiskGauge score={27.5} band="Medium" mediumFrom={25} highAbove={50} />);
    expect(screen.getByTestId("risk-score")).toHaveTextContent("27.5");
    expect(screen.getByTestId("risk-band")).toHaveTextContent("Medium smell risk");
  });
  it("handles no changed methods", () => {
    render(<RiskGauge score={null} band="n/a" mediumFrom={25} highAbove={50} />);
    expect(screen.getByTestId("risk-band")).toHaveTextContent("no changed methods");
  });
});

describe("ScorePanel", () => {
  it("renders the formula and the disclaimer it is given", () => {
    render(<ScorePanel risk={RISK} />);
    const panel = screen.getByTestId("score-panel");
    expect(panel).toHaveTextContent("method points = 1 if any smell is clear");
    expect(panel).toHaveTextContent("not a probability of bugs");
  });
});

describe("MethodsTable", () => {
  it("sorts, filters and selects rows", async () => {
    const onSelect = vi.fn();
    render(<MethodsTable methods={METHODS} onSelect={onSelect} />);
    const table = screen.getByTestId("methods-table");
    const names = () => within(table).getAllByRole("row").slice(1).map((r) => r.querySelectorAll("td")[1]?.textContent);
    expect(names()).toEqual(["alpha", "beta", "gamma"]);            // status order: introduced, unchanged, removed
    await userEvent.click(screen.getByText(/^Method/));
    await userEvent.click(screen.getByText(/^Method/));             // descending by name
    expect(names()).toEqual(["gamma", "beta", "alpha"]);
    await userEvent.selectOptions(screen.getByLabelText("Zone filter"), "borderline");
    expect(names()).toEqual(["alpha"]);
    await userEvent.selectOptions(screen.getByLabelText("Zone filter"), "all");
    await userEvent.type(screen.getByLabelText("Filter by file or method"), "B.java");
    expect(names()).toEqual(["beta"]);
    fireEvent.click(within(table).getByText("beta"));
    expect(onSelect).toHaveBeenCalledWith(METHODS[1]);
  });
});

describe("MethodDrawer", () => {
  it("highlights changed lines and shows the honest note", () => {
    const onClose = vi.fn();
    render(<MethodDrawer method={METHODS[0]} config={CONFIG} onClose={onClose} />);
    const code = screen.getByTestId("code");
    const highlighted = code.querySelectorAll(".bg-amber-400\\/25");
    expect(highlighted).toHaveLength(2);
    expect(screen.getByTestId("note-CM")).toHaveTextContent("Candidate to review, not a verdict");
    expect(screen.getByTestId("method-drawer")).not.toHaveTextContent(/certain|definitely/i);
    fireEvent.keyDown(window, { key: "Escape" });
    expect(onClose).toHaveBeenCalled();
  });
});

describe("parseInput", () => {
  it("routes pull-request URLs and repo + sha", () => {
    expect(parseInput("https://github.com/o/r/pull/7", "abc", "commit")).toEqual({ pr_url: "https://github.com/o/r/pull/7", mode: "commit" });
    expect(parseInput(" https://github.com/o/r ", "abc1234", "commit")).toMatchObject({ repo_url: "https://github.com/o/r", commit_sha: "abc1234" });
    expect(parseInput("https://github.com/o/r", "", "repo", 100)).toMatchObject({ mode: "repo", max_files: 100, commit_sha: undefined });
  });
});
