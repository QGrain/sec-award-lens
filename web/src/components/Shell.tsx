import type { ReactNode } from "react";
import { formatDate } from "../data";

export function Shell({ children, updatedAt }: { children: ReactNode; updatedAt?: string }) {
  const home = () => { window.location.hash = "/"; };
  const repositoryUrl = (import.meta.env.VITE_REPOSITORY_URL as string | undefined)
    ?? "https://github.com/QGrain/sec-award-lens";
  return (
    <>
      <header className="site-header">
        <button className="brand" onClick={home} aria-label="SecAwardLens home">
          <span className="brand-mark" aria-hidden="true"><i /><i /><i /></span>
          <span>SecAward<span>Lens</span></span>
        </button>
        <nav aria-label="Main navigation">
          <a href="#/">Papers &amp; rankings</a>
          <a href="#/methodology">Methodology</a>
          <a href={repositoryUrl} target="_blank" rel="noreferrer">GitHub ↗</a>
        </nav>
      </header>
      <main>{children}</main>
      <footer>
        <div><span className="status-dot" /> OpenAlex data{updatedAt ? ` · refreshed ${formatDate(updatedAt)}` : ""}</div>
        <div>Code Apache-2.0 · Source data retains provider terms</div>
      </footer>
    </>
  );
}
