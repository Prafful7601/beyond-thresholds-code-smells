import { PROJECT } from "../project";
import { REPO_URL_FALLBACK } from "./links";

export default function ProjectCard({ repo, paper }: { repo?: string; paper?: string }) {
  const repoUrl = repo || REPO_URL_FALLBACK;
  return (
    <footer className="mt-16 border-t border-surface-3 bg-white" data-testid="project-card">
      <div className="mx-auto max-w-6xl px-4 py-8 sm:px-6">
        <div className="card relative overflow-hidden p-6 sm:p-8">
          <div className="absolute inset-y-0 left-0 w-1.5 bg-gradient-to-b from-brand to-clean" aria-hidden />
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div className="min-w-0">
              <p className="text-xs font-bold tracking-[0.18em] text-brand">{PROJECT.label}</p>
              <h2 className="mt-2 max-w-3xl text-lg font-bold leading-snug sm:text-xl">{PROJECT.title}</h2>
            </div>
            <span className="chip shrink-0 bg-[#fd6925] px-3 py-1 text-white" title="UN Sustainable Development Goal 9: Industry, Innovation and Infrastructure">{PROJECT.badge}</span>
          </div>
          <div className="mt-5 grid gap-6 text-sm sm:grid-cols-2 lg:grid-cols-3">
            <div>
              <p className="font-semibold text-ink-2">Team</p>
              <ul className="mt-1 space-y-0.5">
                {PROJECT.team.map((m) => (
                  <li key={m.roll}>{m.name} <span className="font-mono text-xs text-ink-3">{m.roll}</span></li>
                ))}
              </ul>
              <p className="mt-2 text-ink-2">{PROJECT.meta}</p>
            </div>
            <div>
              <p className="font-semibold text-ink-2">Supervision</p>
              <p className="mt-1">Supervisor: {PROJECT.supervisor}</p>
              <p>Co-supervisor: {PROJECT.coSupervisor}</p>
              <p className="mt-2 text-ink-2">{PROJECT.institute}</p>
            </div>
            <div>
              <p className="font-semibold text-ink-2">Links</p>
              <p className="mt-1"><a className="text-brand hover:underline" href={repoUrl} target="_blank" rel="noreferrer">GitHub repository</a></p>
              <p><a className="text-brand hover:underline" href={`${repoUrl}/blob/main/results/results.md`} target="_blank" rel="noreferrer">Paper results</a>
                {paper ? <span className="block text-xs text-ink-3">{paper}</span> : null}</p>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
}
