import type { ConferenceSummary as Summary } from "../types";
import { usePreferences } from "../preferences";

const color: Record<string, string> = {
  "ieee-sp": "var(--ieee)",
  "usenix-security": "var(--usenix)",
  "acm-ccs": "var(--ccs)",
  ndss: "var(--ndss)",
};

export function ConferenceSummary({ summaries }: { summaries: Summary[] }) {
  const { language } = usePreferences();
  const text = language === "zh" ? {
    aria: "会议统计摘要",
    median: "引用中位数",
    average: "平均值",
    range: "观测范围",
    awards: "篇获奖论文",
    matched: "篇已匹配",
  } : {
    aria: "Conference summaries",
    median: "median citations",
    average: "average",
    range: "observed range",
    awards: "awards",
    matched: "matched",
  };
  return (
    <section className="summary-grid" aria-label={text.aria}>
      {summaries.map((summary) => (
        <article className="summary-card" key={summary.conference.id} style={{ "--accent": color[summary.conference.id] } as React.CSSProperties}>
          <div className="eyebrow"><span />{summary.conference.short_name}</div>
          <strong>{summary.citations.median ?? "—"}</strong>
          <span className="metric-label">{text.median}</span>
          <div className="summary-stat-row">
            <span><b>{summary.citations.mean?.toFixed(1) ?? "—"}</b>{text.average}</span>
            <span><b>{summary.citations.min ?? "—"}–{summary.citations.max ?? "—"}</b>{text.range}</span>
          </div>
          <div className="summary-meta">
            <span>{summary.award_count} {text.awards}</span>
            <span>{summary.cited_paper_count}/{summary.award_count} {text.matched}</span>
          </div>
        </article>
      ))}
    </section>
  );
}
