import type { ConferenceSummary as Summary } from "../types";

const color: Record<string, string> = {
  "ieee-sp": "var(--ieee)",
  "usenix-security": "var(--usenix)",
  "acm-ccs": "var(--ccs)",
  ndss: "var(--ndss)",
};

export function ConferenceSummary({ summaries }: { summaries: Summary[] }) {
  return (
    <section className="summary-grid" aria-label="Conference summaries">
      {summaries.map((summary) => (
        <article className="summary-card" key={summary.conference.id} style={{ "--accent": color[summary.conference.id] } as React.CSSProperties}>
          <div className="eyebrow"><span />{summary.conference.short_name}</div>
          <strong>{summary.citations.median ?? "—"}</strong>
          <span className="metric-label">median citations</span>
          <div className="summary-stat-row">
            <span><b>{summary.citations.mean?.toFixed(1) ?? "—"}</b>average</span>
            <span><b>{summary.citations.min ?? "—"}–{summary.citations.max ?? "—"}</b>observed range</span>
          </div>
          <div className="summary-meta">
            <span>{summary.award_count} awards</span>
            <span>{summary.cited_paper_count}/{summary.award_count} matched</span>
          </div>
        </article>
      ))}
    </section>
  );
}
