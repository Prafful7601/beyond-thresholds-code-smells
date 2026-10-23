import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { _resetConfigCache } from "../useConfig";
import { CONFIG } from "../test/fixtures";
import About from "./About";
import ProjectCard from "../components/ProjectCard";

beforeEach(() => {
  _resetConfigCache();
  vi.stubGlobal("fetch", vi.fn(async () => new Response(JSON.stringify(CONFIG), { status: 200 })));
});

it("About explains what the tool does not claim and why MA is excluded", async () => {
  render(<MemoryRouter><About /></MemoryRouter>);
  await waitFor(() => expect(screen.getByText(/MA:/)).toBeInTheDocument());
  expect(screen.getByText(/candidate to review, not a verdict/i)).toBeInTheDocument();
  expect(screen.getByText(/not a probability of bugs/i)).toBeInTheDocument();
});

it("Project card shows the team, supervisors and SDG badge", () => {
  render(<ProjectCard />);
  const card = screen.getByTestId("project-card");
  expect(card).toHaveTextContent("MAJOR PROJECT · 2026–27");
  expect(card).toHaveTextContent("202510116100161");
  expect(card).toHaveTextContent("Rabi N. Panda");
  expect(card).toHaveTextContent("SDG 9");
});
