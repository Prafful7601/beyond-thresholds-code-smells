import { NavLink, Outlet } from "react-router-dom";
import ProjectCard from "./ProjectCard";
import { useConfig } from "../useConfig";

const NAV = [["/", "Analyze"], ["/history", "History"], ["/research", "Research findings"], ["/about", "About"]] as const;

export default function Layout() {
  const { config } = useConfig();
  return (
    <div className="flex min-h-screen flex-col">
      <header className="sticky top-0 z-30 border-b border-surface-3 bg-white/90 backdrop-blur">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3 px-4 py-3 sm:px-6">
          <NavLink to="/" className="flex items-center gap-2 text-lg font-extrabold tracking-tight">
            <img src="/favicon.svg" alt="" className="h-7 w-7" /> CodeSniff
          </NavLink>
          <nav className="flex flex-wrap gap-1 text-sm">
            {NAV.map(([to, label]) => (
              <NavLink key={to} to={to} end={to === "/"}
                className={({ isActive }) => `rounded-lg px-3 py-1.5 font-medium ${isActive ? "bg-brand-light text-brand" : "text-ink-2 hover:bg-surface-2"}`}>
                {label}
              </NavLink>
            ))}
          </nav>
        </div>
      </header>
      <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-8 sm:px-6"><Outlet /></main>
      <ProjectCard repo={config?.links.repository} />
    </div>
  );
}
