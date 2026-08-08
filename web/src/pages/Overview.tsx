import { useEffect, useMemo, useState } from "react";
import type { EChartsCoreOption } from "echarts/core";
import { Chart } from "../components/Chart";
import { ConferenceSummary } from "../components/ConferenceSummary";
import { compactNumber, formatDate } from "../data";
import type { Conference, RankingRow, YearData } from "../types";

const colors: Record<string, string> = {
  "ieee-sp": "#45d6ad",
  "usenix-security": "#ffc857",
  "acm-ccs": "#ff7a8a",
  ndss: "#8e92ff",
};

const PAGE_SIZE = 12;
type Metric = "total" | "c3";
type ComparisonView = "typical" | "range" | "sensitivity" | "age";

function valueFor(row: RankingRow, metric: Metric) {
  if (!row.citation) return null;
  return metric === "total"
    ? row.citation.total_citations
    : (row.citation.citations_first_3_years ?? null);
}

function topicFor(row: RankingRow) {
  return row.primary_topic ?? row.enrichment?.primary_topic ?? null;
}

function median(values: number[]) {
  if (!values.length) return null;
  const ordered = [...values].sort((a, b) => a - b);
  const middle = Math.floor(ordered.length / 2);
  return ordered.length % 2
    ? ordered[middle]
    : (ordered[middle - 1] + ordered[middle]) / 2;
}

function fiveNumber(values: number[]) {
  const ordered = [...values].sort((a, b) => a - b);
  const middle = Math.floor(ordered.length / 2);
  const lower = ordered.slice(0, middle).length ? ordered.slice(0, middle) : ordered;
  const upperStart = middle + (ordered.length % 2);
  const upper = ordered.slice(upperStart).length ? ordered.slice(upperStart) : ordered;
  return [ordered[0], median(lower) ?? 0, median(ordered) ?? 0, median(upper) ?? 0, ordered.at(-1) ?? 0];
}

function ComparisonCharts({ rows, metric }: { rows: RankingRow[]; metric: Metric }) {
  const [view, setView] = useState<ComparisonView>("typical");
  const groups = useMemo(() => [...new Map(rows.map((row) => [row.conference.id, row.conference])).values()]
    .map((conference) => ({
      conference,
      rows: rows.filter((row) => row.conference.id === conference.id && valueFor(row, metric) !== null),
    })), [metric, rows]);

  const option = useMemo<EChartsCoreOption>(() => {
    const labels = groups.map(({ conference }) => conference.short_name);
    const values = groups.map((group) => group.rows.map((row) => valueFor(row, metric) as number));
    const grid = { left: 75, right: 35, top: 45, bottom: 55, containLabel: true };
    const splitLine = { lineStyle: { color: "#dce5df" } };

    if (view === "range") {
      return {
        animationDuration: 450,
        grid,
        tooltip: {
          trigger: "item",
          formatter: (params: unknown) => {
            const item = params as { name: string; data: number[] };
            const [low, q1, med, q3, high] = item.data.map((value) => value - 1);
            return `<b>${item.name}</b><br>min ${low} · Q1 ${q1} · median ${med} · Q3 ${q3} · max ${high}`;
          },
        },
        xAxis: {
          type: "log",
          min: 1,
          name: "Citations + 1 (log scale)",
          nameLocation: "middle",
          nameGap: 34,
          splitLine,
          axisLabel: { formatter: (value: number) => String(Math.max(0, value - 1)) },
        },
        yAxis: { type: "category", data: labels, axisTick: { show: false }, axisLine: { show: false } },
        series: [{
          type: "boxplot",
          data: values.map((items, index) => ({
            name: labels[index],
            value: fiveNumber(items).map((value) => value + 1),
            itemStyle: { color: colors[groups[index].conference.id], borderColor: "#28463d" },
          })),
        }],
      };
    }

    if (view === "sensitivity") {
      const points = groups.flatMap((group, conferenceIndex) => {
        const total = group.rows.reduce((sum, row) => sum + (valueFor(row, metric) ?? 0), 0);
        const baseline = group.rows.length ? total / group.rows.length : 0;
        return group.rows.map((row) => ({
          value: [group.rows.length > 1 ? (total - (valueFor(row, metric) ?? 0)) / (group.rows.length - 1) - baseline : 0, conferenceIndex],
          name: row.paper.canonical_title,
          conference: group.conference.short_name,
          itemStyle: { color: colors[group.conference.id] },
        }));
      });
      return {
        animationDuration: 450,
        grid,
        tooltip: {
          trigger: "item",
          formatter: (params: unknown) => {
            const point = params as { data: { name: string; conference: string; value: [number, number] } };
            const delta = point.data.value[0];
            return `<b>${point.data.conference}</b><br>${point.data.name}<br>mean change if removed: ${delta >= 0 ? "+" : ""}${delta.toFixed(1)}`;
          },
        },
        xAxis: {
          type: "value",
          name: "Change in conference mean if one paper is removed",
          nameLocation: "middle",
          nameGap: 34,
          splitLine,
        },
        yAxis: { type: "category", data: labels, axisTick: { show: false }, axisLine: { show: false } },
        series: [{
          type: "scatter",
          data: points,
          symbolSize: 10,
          markLine: { silent: true, symbol: "none", lineStyle: { color: "#6f817a" }, data: [{ xAxis: 0 }] },
        }],
      };
    }

    if (view === "age") {
      const current = groups.map((group) => median(group.rows.flatMap((row) => row.citation ? [row.citation.total_citations] : [])));
      const firstThree = groups.map((group) => median(group.rows.flatMap((row) => row.citation?.citations_first_3_years !== undefined ? [row.citation.citations_first_3_years] : [])));
      return {
        animationDuration: 450,
        grid,
        tooltip: { trigger: "axis", axisPointer: { type: "shadow" } },
        legend: { top: 4 },
        xAxis: { type: "category", data: labels, axisTick: { show: false } },
        yAxis: { type: "value", name: "Median citations", minInterval: 1, splitLine },
        series: [
          { type: "bar", name: "Current", data: current, itemStyle: { color: "#19342c" }, barMaxWidth: 34 },
          { type: "bar", name: "First 3 years", data: firstThree, itemStyle: { color: "#45d6ad" }, barMaxWidth: 34 },
        ],
      };
    }

    return {
      animationDuration: 450,
      grid,
      tooltip: { trigger: "axis", axisPointer: { type: "shadow" } },
      legend: { top: 4 },
      xAxis: { type: "category", data: labels, axisTick: { show: false } },
      yAxis: { type: "value", name: "Citations", minInterval: 1, splitLine },
      series: [
        { type: "bar", name: "Median", data: values.map((items) => median(items)), itemStyle: { color: "#19342c" }, barMaxWidth: 34 },
        { type: "bar", name: "Average", data: values.map((items) => items.length ? items.reduce((sum, value) => sum + value, 0) / items.length : null), itemStyle: { color: "#45d6ad" }, barMaxWidth: 34 },
      ],
    };
  }, [groups, metric, view]);

  const descriptions: Record<ComparisonView, string> = {
    typical: "Median and average describe a typical awarded paper without treating a conference’s number of awards as impact.",
    range: "A five-number range on a citations + 1 log scale makes skew and outliers visible; the center line is the median.",
    sensitivity: "Each point shows how much a conference mean changes when that paper is removed. This is sensitivity analysis, not predictive cross-validation.",
    age: "The fixed three-year window gives papers the same citation-age budget; current counts remain useful but are age-dependent.",
  };

  return (
    <>
      <div className="comparison-tabs" role="tablist" aria-label="Conference comparison view">
        <button className={view === "typical" ? "active" : ""} onClick={() => setView("typical")}>Median & average</button>
        <button className={view === "range" ? "active" : ""} onClick={() => setView("range")}>Log range</button>
        <button className={view === "sensitivity" ? "active" : ""} onClick={() => setView("sensitivity")}>Leave-one-out sensitivity</button>
        <button className={view === "age" ? "active" : ""} onClick={() => setView("age")}>Age window</button>
      </div>
      <p className="comparison-note">{descriptions[view]}</p>
      <Chart option={option} height={360} label={`${view} conference citation comparison`} />
    </>
  );
}

export function Overview({ data, conferences }: { data: YearData; conferences: Conference[] }) {
  const [active, setActive] = useState<Set<string>>(new Set(conferences.map((item) => item.id)));
  const [metric, setMetric] = useState<Metric>("total");
  const [page, setPage] = useState(1);
  const filtered = useMemo(() => data.rows
    .filter((row) => active.has(row.conference.id))
    .sort((a, b) => (valueFor(b, metric) ?? -1) - (valueFor(a, metric) ?? -1)), [active, data.rows, metric]);
  const matched = data.rows.filter((row) => row.citation).length;
  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const visibleRows = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);
  useEffect(() => setPage(1), [active, metric]);

  const toggle = (id: string) => setActive((current) => {
    const next = new Set(current);
    if (next.has(id) && next.size > 1) next.delete(id); else next.add(id);
    return next;
  });

  return (
    <>
      <section className="hero">
        <div className="hero-copy">
          <p className="kicker">Citation analytics for top-tier security research</p>
          <h1>Award-winning security papers and their <em>citation impact.</em></h1>
          <p className="lede">SecAwardLens tracks Best, Outstanding, and Distinguished Paper winners from IEEE S&amp;P, USENIX Security, ACM CCS, and NDSS. It connects official award announcements to verified scholarly records so researchers can compare citation impact across papers, conferences, and publication-age windows.</p>
        </div>
        <aside className="hero-stat">
          <div><strong>{data.rows.length}</strong><span>award-winning papers</span></div>
          <div><strong>{matched}</strong><span>citation-linked records</span></div>
          <small>2023 conference coverage · snapshot {formatDate(data.generated_at)}</small>
        </aside>
      </section>

      <section className="control-bar">
        <div className="control-group"><span>Year</span><span className="year-badge">{data.year}</span></div>
        <div className="conference-toggles" aria-label="Filter conferences">
          {conferences.map((conference) => <button key={conference.id} className={active.has(conference.id) ? "active" : ""} onClick={() => toggle(conference.id)}><i style={{ background: colors[conference.id] }} />{conference.short_name}</button>)}
        </div>
        <div className="segmented" aria-label="Citation metric">
          <button className={metric === "total" ? "active" : ""} onClick={() => setMetric("total")}>Current</button>
          <button className={metric === "c3" ? "active" : ""} onClick={() => setMetric("c3")}>First 3 years</button>
        </div>
        <button className="capture-button" onClick={() => window.print()} title="Open a clean print or PDF view">Print / capture</button>
      </section>
      <aside className="review-banner">
        <span>Coverage note</span>
        All 47 official award records are included; five papers do not yet have a verified OpenAlex entity and are shown without citation counts.
        <a href="#/methodology">How coverage is verified →</a>
      </aside>

      <ConferenceSummary summaries={data.conference_summaries} />

      <section className="panel ranking-panel">
        <div className="panel-heading">
          <div><p className="kicker">Paper ranking</p><h2>{metric === "total" ? "Award paper citation ranking" : "Award paper impact in a fixed three-year window"}</h2></div>
          <span className="source-pill">Source · OpenAlex</span>
        </div>
        <div className="ranking-header" aria-hidden="true">
          <span>Rank</span><span>Paper</span><span>Topic</span><span>Conference</span><span>Citations</span>
        </div>
        <div className="ranking-list">
          {visibleRows.map((row, index) => (
            <a className="ranking-row" key={row.paper.id} href={`#/paper/${row.paper.id}`} title={row.paper.canonical_title}>
              <span className="rank">{String((page - 1) * PAGE_SIZE + index + 1).padStart(2, "0")}</span>
              <span className="paper-copy"><b>{row.paper.canonical_title}</b><small>{row.paper.authors.slice(0, 3).map((author) => author.name).join(", ")}{row.paper.authors.length > 3 ? " et al." : ""}</small></span>
              <span className="topic-cell" title={topicFor(row) ? "Topic assigned by OpenAlex" : "No OpenAlex topic is available for this paper"}>{topicFor(row)?.display_name ?? "Not indexed"}</span>
              <span className="conference-cell"><i style={{ background: colors[row.conference.id] }} />{row.conference.short_name}</span>
              <span className="citation-number">{row.citation ? compactNumber(valueFor(row, metric) ?? 0) : "—"}<small>{row.citation ? "citations" : "unmatched"}</small></span>
            </a>
          ))}
        </div>
        <div className="pagination">
          <span>Showing {(page - 1) * PAGE_SIZE + 1}–{Math.min(page * PAGE_SIZE, filtered.length)} of {filtered.length}</span>
          <div><button disabled={page === 1} onClick={() => setPage((value) => value - 1)}>← Previous</button><b>{page} / {totalPages}</b><button disabled={page === totalPages} onClick={() => setPage((value) => value + 1)}>Next →</button></div>
        </div>
      </section>

      <section className="panel comparison-panel">
        <div className="panel-heading"><div><p className="kicker">Conference comparison</p><h2>Compare distributions, not raw totals</h2></div><span className="source-pill">{metric === "total" ? "Current citations" : "First 3 years"}</span></div>
        <ComparisonCharts rows={filtered} metric={metric} />
      </section>
    </>
  );
}
