import { useEffect, useMemo, useState } from "react";
import type { EChartsCoreOption } from "echarts/core";
import { Chart } from "../components/Chart";
import { compactNumber, formatDate, loadPaper } from "../data";
import type { PaperData } from "../types";

export function PaperDetail({ id }: { id: string }) {
  const [data, setData] = useState<PaperData | null>(null);
  const [error, setError] = useState("");
  useEffect(() => { loadPaper(id).then(setData).catch((reason: Error) => setError(reason.message)); }, [id]);
  const latest = data?.citation_history.openalex?.at(-1);
  const yearlyOption = useMemo<EChartsCoreOption>(() => ({
    grid: { left: 45, right: 15, top: 18, bottom: 42 },
    tooltip: { trigger: "axis" },
    xAxis: { type: "category", data: latest?.citations_by_citing_year.map((item) => item.year) ?? [], axisTick: { show: false } },
    yAxis: { type: "value", minInterval: 1, splitLine: { lineStyle: { color: "#dce5df" } } },
    series: [{ type: "bar", data: latest?.citations_by_citing_year.map((item) => item.count) ?? [], itemStyle: { color: "#45d6ad", borderRadius: [4, 4, 0, 0] }, barMaxWidth: 42 }],
  }), [latest]);
  if (error) return <section className="empty-state"><h1>Paper not found</h1><p>{error}</p><a href="#/">Return to rankings</a></section>;
  if (!data) return <div className="loading">Loading paper record…</div>;
  const doi = data.paper.identifiers.find((item) => item.scheme === "doi");
  const binding = data.bindings.find((item) => item.provider === "openalex");
  const affiliations = new Map(
    data.enrichment?.authors.map((author) => [
      author.author_name,
      [...new Set(author.affiliations.map((item) => item.display_name))],
    ]) ?? [],
  );
  const hasAffiliations = [...affiliations.values()].some((items) => items.length);
  return (
    <>
      <section className="paper-hero">
        <a href="#/" className="back-link">← All 2023 papers</a>
        <div className="paper-venue-line">
          <strong>{data.paper.venue_name}</strong>
          <span>{data.awards[0]?.raw_award_name}</span>
        </div>
        <h1>{data.paper.canonical_title}</h1>
        <p className="authors" aria-label="Authors and affiliations">
          {data.paper.authors.map((author, index) => {
            const institutions = affiliations.get(author.name) ?? [];
            return <span key={author.name}><b>{author.name}</b>{institutions.length ? <small> ({institutions.join(", ")})</small> : null}{index < data.paper.authors.length - 1 ? ", " : ""}</span>;
          })}
        </p>
        {hasAffiliations && <small className="affiliation-note">Affiliations are supplied by OpenAlex and may be incomplete.</small>}
        {data.enrichment?.primary_topic && <p className="paper-topic"><span>OpenAlex topic</span>{data.enrichment.primary_topic.display_name}</p>}
        <div className="paper-links">
          {data.paper.official_paper_url && <a href={data.paper.official_paper_url} target="_blank" rel="noreferrer">Official paper ↗</a>}
          {doi && <a href={`https://doi.org/${doi.value}`} target="_blank" rel="noreferrer">DOI ↗</a>}
          {binding?.external_id && <a href={`https://openalex.org/${binding.external_id}`} target="_blank" rel="noreferrer">OpenAlex ↗</a>}
        </div>
      </section>
      <section className="paper-metrics">
        <article><span>Current citations</span><strong>{latest ? compactNumber(latest.total_citations) : "—"}</strong><small>{latest ? `snapshot ${formatDate(latest.retrieved_at)}` : "No verified OpenAlex entity"}</small></article>
        <article><span>First 3 years</span><strong>{latest ? latest.citations_by_citing_year.filter((item) => item.year >= data.paper.publication_year && item.year < data.paper.publication_year + 3).reduce((sum, item) => sum + item.count, 0) : "—"}</strong><small>publication-age window</small></article>
        <article><span>Entity match</span><strong className="match-status">{binding?.status.replace("_", " ") ?? "pending"}</strong><small>{binding?.method?.replace("_", " ") ?? "requires review"}</small></article>
      </section>
      <section className="paper-grid">
        <article className="panel">
          <div className="panel-heading"><div><p className="kicker">Citation profile</p><h2>Citations by citing year</h2></div></div>
          {latest && latest.citations_by_citing_year.length ? <Chart option={yearlyOption} height={320} label="Citations received by publication year of citing works" /> : <p className="empty-chart">No year-level citation counts are available yet.</p>}
          <p className="chart-note">This is the citing works’ publication year—not a historical snapshot of what the counter displayed then.</p>
        </article>
        <aside className="provenance-card">
          <p className="kicker">Audit trail</p><h2>Why this record is trustworthy</h2>
          <dl>
            <div><dt>Award source</dt><dd><a href={data.awards[0]?.official_source.url} target="_blank" rel="noreferrer">Official conference page ↗</a></dd></div>
            <div><dt>Raw award label</dt><dd>{data.awards[0]?.raw_award_name}</dd></div>
            <div><dt>Match decision</dt><dd>{binding?.status.replace("_", " ") ?? "pending"}{binding?.confidence != null ? ` · ${Math.round(binding.confidence * 100)}% confidence` : " · requires review"}</dd></div>
            <div><dt>Citation source</dt><dd>OpenAlex work {binding?.external_id ?? "not resolved"}</dd></div>
            <div><dt>Snapshot history</dt><dd>{data.citation_history.openalex?.length ?? 0} immutable observation(s)</dd></div>
            {binding?.review_notes && <div><dt>Review note</dt><dd>{binding.review_notes}</dd></div>}
          </dl>
        </aside>
      </section>
    </>
  );
}
