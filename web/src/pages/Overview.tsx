import { useEffect, useMemo, useState } from "react";
import type { EChartsCoreOption } from "echarts/core";
import { Chart } from "../components/Chart";
import { ConferenceSummary } from "../components/ConferenceSummary";
import { compactNumber, formatDate, providerAbbreviation, providerName } from "../data";
import { usePreferences } from "../preferences";
import type {
  Citation,
  Conference,
  ConferenceSummary as Summary,
  Provider,
  RankingRow,
  YearData,
} from "../types";

const colors: Record<string, string> = {
  "ieee-sp": "#45d6ad",
  "usenix-security": "#ffc857",
  "acm-ccs": "#ff7a8a",
  ndss: "#8e92ff",
};

const PAGE_SIZE = 12;
type Metric = "total" | "c3";
type ComparisonView = "typical" | "range" | "sensitivity" | "age";
type DisplayRow = RankingRow & { citation: Citation | null };

function valueFor(row: DisplayRow, metric: Metric) {
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

function ComparisonCharts({ rows, metric }: { rows: DisplayRow[]; metric: Metric }) {
  const { language, resolvedTheme } = usePreferences();
  const text = language === "zh" ? {
    aria: "会议引用比较视图",
    typical: "中位数与平均值",
    range: "对数范围",
    sensitivity: "逐篇剔除敏感性",
    age: "固定年限窗口",
    citations: "引用量",
    median: "中位数",
    average: "平均值",
    current: "当前引用",
    firstThree: "发表后三年",
    medianCitations: "引用中位数",
    citationsLog: "引用量 + 1（对数尺度）",
    meanChange: "剔除一篇论文后会议平均值的变化",
    min: "最小值",
    q1: "Q1",
    med: "中位数",
    q3: "Q3",
    max: "最大值",
    change: "剔除后的平均值变化",
    descriptions: {
      typical: "中位数与平均值描述典型获奖论文，不把某会议的获奖数量误当作影响力。",
      range: "引用量 + 1 的对数尺度五数概括可展示偏态与离群值；箱体中心线为中位数。",
      sensitivity: "每个点表示剔除该论文后会议平均值的变化。这是敏感性分析，并非预测性留一交叉验证。",
      age: "固定三年窗口为论文提供相同的引用积累时间；当前引用量仍有用，但受论文年龄影响。",
    },
  } : {
    aria: "Conference comparison view",
    typical: "Median & average",
    range: "Log range",
    sensitivity: "Leave-one-out sensitivity",
    age: "Age window",
    citations: "Citations",
    median: "Median",
    average: "Average",
    current: "Current",
    firstThree: "First 3 years",
    medianCitations: "Median citations",
    citationsLog: "Citations + 1 (log scale)",
    meanChange: "Change in conference mean if one paper is removed",
    min: "min",
    q1: "Q1",
    med: "median",
    q3: "Q3",
    max: "max",
    change: "mean change if removed",
    descriptions: {
      typical: "Median and average describe a typical awarded paper without treating a conference’s number of awards as impact.",
      range: "A five-number range on a citations + 1 log scale makes skew and outliers visible; the center line is the median.",
      sensitivity: "Each point shows how much a conference mean changes when that paper is removed. This is sensitivity analysis, not predictive cross-validation.",
      age: "The fixed three-year window gives papers the same citation-age budget; current counts remain useful but are age-dependent.",
    },
  };
  const [view, setView] = useState<ComparisonView>("typical");
  const hasAgeWindow = rows.some((row) => row.citation?.citations_first_3_years != null);
  useEffect(() => {
    if (!hasAgeWindow && view === "age") setView("typical");
  }, [hasAgeWindow, view]);
  const groups = useMemo(() => [...new Map(rows.map((row) => [row.conference.id, row.conference])).values()]
    .map((conference) => ({
      conference,
      rows: rows.filter((row) => row.conference.id === conference.id && valueFor(row, metric) !== null),
    })), [metric, rows]);

  const option = useMemo<EChartsCoreOption>(() => {
    const labels = groups.map(({ conference }) => conference.short_name);
    const values = groups.map((group) => group.rows.map((row) => valueFor(row, metric) as number));
    const grid = { left: 75, right: 35, top: 45, bottom: 55, containLabel: true };
    const dark = resolvedTheme === "dark";
    const splitLine = { lineStyle: { color: dark ? "#344740" : "#dce5df" } };
    const axisLabel = { color: dark ? "#a9bcb5" : "#53655f" };
    const axisNameTextStyle = { color: dark ? "#a9bcb5" : "#53655f" };
    const tooltip = { backgroundColor: dark ? "#172a24" : "#fff", borderColor: dark ? "#42574f" : "#d5dfd8", textStyle: { color: dark ? "#edf5f1" : "#152a24" } };

    if (view === "range") {
      return {
        animationDuration: 450,
        grid,
        tooltip: {
          trigger: "item",
          formatter: (params: unknown) => {
            const item = params as { name: string; data: number[] };
            const [low, q1, med, q3, high] = item.data.map((value) => value - 1);
            return `<b>${item.name}</b><br>${text.min} ${low} · ${text.q1} ${q1} · ${text.med} ${med} · ${text.q3} ${q3} · ${text.max} ${high}`;
          },
          ...tooltip,
        },
        xAxis: {
          type: "log",
          min: 1,
          name: text.citationsLog,
          nameLocation: "middle",
          nameGap: 34,
          splitLine,
          axisLabel: { ...axisLabel, formatter: (value: number) => String(Math.max(0, value - 1)) },
          nameTextStyle: axisNameTextStyle,
        },
        yAxis: { type: "category", data: labels, axisTick: { show: false }, axisLine: { show: false }, axisLabel },
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
            return `<b>${point.data.conference}</b><br>${point.data.name}<br>${text.change}: ${delta >= 0 ? "+" : ""}${delta.toFixed(1)}`;
          },
          ...tooltip,
        },
        xAxis: {
          type: "value",
          name: text.meanChange,
          nameLocation: "middle",
          nameGap: 34,
          splitLine,
          axisLabel,
          nameTextStyle: axisNameTextStyle,
        },
        yAxis: { type: "category", data: labels, axisTick: { show: false }, axisLine: { show: false }, axisLabel },
        series: [{
          type: "scatter",
          data: points,
          symbolSize: 10,
          markLine: { silent: true, symbol: "none", lineStyle: { color: dark ? "#8ca099" : "#6f817a" }, data: [{ xAxis: 0 }] },
        }],
      };
    }

    if (view === "age") {
      const current = groups.map((group) => median(group.rows.flatMap((row) => row.citation ? [row.citation.total_citations] : [])));
      const firstThree = groups.map((group) => median(group.rows.flatMap((row) => row.citation?.citations_first_3_years != null ? [row.citation.citations_first_3_years] : [])));
      return {
        animationDuration: 450,
        grid,
        tooltip: { trigger: "axis", axisPointer: { type: "shadow" }, ...tooltip },
        legend: { top: 4, textStyle: axisLabel },
        xAxis: { type: "category", data: labels, axisTick: { show: false }, axisLabel },
        yAxis: { type: "value", name: text.medianCitations, minInterval: 1, splitLine, axisLabel, nameTextStyle: axisNameTextStyle },
        series: [
          { type: "bar", name: text.current, data: current, itemStyle: { color: dark ? "#7aa99b" : "#19342c" }, barMaxWidth: 34 },
          { type: "bar", name: text.firstThree, data: firstThree, itemStyle: { color: "#45d6ad" }, barMaxWidth: 34 },
        ],
      };
    }

    return {
      animationDuration: 450,
      grid,
      tooltip: { trigger: "axis", axisPointer: { type: "shadow" }, ...tooltip },
      legend: { top: 4, textStyle: axisLabel },
      xAxis: { type: "category", data: labels, axisTick: { show: false }, axisLabel },
      yAxis: { type: "value", name: text.citations, minInterval: 1, splitLine, axisLabel, nameTextStyle: axisNameTextStyle },
      series: [
        { type: "bar", name: text.median, data: values.map((items) => median(items)), itemStyle: { color: dark ? "#7aa99b" : "#19342c" }, barMaxWidth: 34 },
        { type: "bar", name: text.average, data: values.map((items) => items.length ? items.reduce((sum, value) => sum + value, 0) / items.length : null), itemStyle: { color: "#45d6ad" }, barMaxWidth: 34 },
      ],
    };
  }, [groups, metric, resolvedTheme, text, view]);

  return (
    <>
      <div className="comparison-tabs" role="tablist" aria-label={text.aria}>
        <button className={view === "typical" ? "active" : ""} onClick={() => setView("typical")}>{text.typical}</button>
        <button className={view === "range" ? "active" : ""} onClick={() => setView("range")}>{text.range}</button>
        <button className={view === "sensitivity" ? "active" : ""} onClick={() => setView("sensitivity")}>{text.sensitivity}</button>
        <button disabled={!hasAgeWindow} className={view === "age" ? "active" : ""} onClick={() => setView("age")}>{text.age}</button>
      </div>
      <p className="comparison-note">{text.descriptions[view]}</p>
      <Chart option={option} height={360} label={`${view} conference citation comparison`} />
    </>
  );
}

export function Overview({
  data,
  conferences,
  citationSources,
  preferredCitationSource,
  initialCitationSource,
  availableYears,
  onYearChange,
}: {
  data: YearData;
  conferences: Conference[];
  citationSources: Provider[];
  preferredCitationSource: Provider;
  initialCitationSource?: Provider | null;
  availableYears: number[];
  onYearChange: (year: number) => void;
}) {
  const { language, locale } = usePreferences();
  const text = language === "zh" ? {
    kicker: "安全顶会获奖论文引用分析",
    titleLead: "安全顶会获奖论文",
    titleImpact: "及其引用影响力",
    lede: "SecAwardLens 收录 IEEE S&P、USENIX Security、ACM CCS 与 NDSS 的 Best、Outstanding 和 Distinguished Paper 获奖论文，并将官方奖项记录与经过核验的学术实体相连，以便研究者从论文、会议及发表后三年等固定时间窗口比较引用影响力。",
    papers: "篇获奖论文",
    linked: "篇已关联引用数据",
    coverage: "四个会议覆盖",
    snapshot: "数据快照",
    year: "年份",
    filter: "筛选会议",
    metric: "引用指标",
    sourceMetric: "引用来源",
    scholarViaSerpApi: "Google Scholar（经由 SerpApi）",
    scholarViaScraperApi: "Google Scholar（经由 ScraperAPI）",
    scholarViaMixed: "Google Scholar（经由多个服务）",
    current: "当前",
    firstThree: "发表后三年",
    capture: "打印 / 截图",
    captureTitle: "打开适合打印或导出 PDF 的简洁视图",
    coverageNote: "覆盖说明",
    verify: "了解覆盖核验方式 →",
    ranking: "论文排名",
    rankingCurrent: "获奖论文引用量排名",
    rankingWindow: "获奖论文发表后三年引用量排名",
    source: "来源",
    rank: "排名",
    paper: "论文",
    topic: "主题",
    conference: "会议",
    citations: "引用量",
    topicOpenAlex: "主题由 OpenAlex 自动分配",
    topicUnavailable: "该论文暂无 OpenAlex 主题",
    notIndexed: "暂无",
    unmatched: "未匹配",
    showing: "当前显示",
    of: "共",
    previous: "上一页",
    next: "下一页",
    comparison: "会议比较",
    distributions: "比较分布，而不是引用总量",
  } : {
    kicker: "Citation analytics for top-tier security research",
    titleLead: "Award-winning security papers",
    titleImpact: "and their citation impact",
    lede: "SecAwardLens tracks Best, Outstanding, and Distinguished Paper winners from IEEE S&P, USENIX Security, ACM CCS, and NDSS. It connects official award announcements to verified scholarly records so researchers can compare citation impact across papers, conferences, and publication-age windows.",
    papers: "award-winning papers",
    linked: "citation-linked records",
    coverage: "four-conference coverage",
    snapshot: "snapshot",
    year: "Year",
    filter: "Filter conferences",
    metric: "Citation metric",
    sourceMetric: "Citation source",
    scholarViaSerpApi: "Google Scholar via SerpApi",
    scholarViaScraperApi: "Google Scholar via ScraperAPI",
    scholarViaMixed: "Google Scholar via multiple services",
    current: "Current",
    firstThree: "First 3 years",
    capture: "Print / capture",
    captureTitle: "Open a clean print or PDF view",
    coverageNote: "Coverage note",
    verify: "How coverage is verified →",
    ranking: "Paper ranking",
    rankingCurrent: "Award paper citation ranking",
    rankingWindow: "Award paper impact in a fixed three-year window",
    source: "Source",
    rank: "Rank",
    paper: "Paper",
    topic: "Topic",
    conference: "Conference",
    citations: "Citations",
    topicOpenAlex: "Topic assigned by OpenAlex",
    topicUnavailable: "No OpenAlex topic is available for this paper",
    notIndexed: "Not indexed",
    unmatched: "unmatched",
    showing: "Showing",
    of: "of",
    previous: "Previous",
    next: "Next",
    comparison: "Conference comparison",
    distributions: "Compare distributions, not raw totals",
  };
  const [active, setActive] = useState<Set<string>>(new Set(conferences.map((item) => item.id)));
  const [metric, setMetric] = useState<Metric>("total");
  const initialSource = initialCitationSource && citationSources.includes(initialCitationSource)
    ? initialCitationSource
    : citationSources.includes(preferredCitationSource)
      ? preferredCitationSource
      : citationSources[0] ?? "openalex";
  const [source, setSource] = useState<Provider>(initialSource);
  const [page, setPage] = useState(1);
  const sourceRows = useMemo<DisplayRow[]>(() => data.rows.map((row) => ({
    ...row,
    citation: row.citations[source] ?? null,
  })), [data.rows, source]);
  const filtered = useMemo(() => sourceRows
    .filter((row) => active.has(row.conference.id))
    .sort((a, b) => (valueFor(b, metric) ?? -1) - (valueFor(a, metric) ?? -1)), [active, metric, sourceRows]);
  const matched = sourceRows.filter((row) => row.citation).length;
  const hasAgeMetric = sourceRows.some((row) => row.citation?.citations_first_3_years != null);
  const sourceName = providerName(source);
  const scholarServices = new Set(sourceRows.flatMap((row) => row.citation
    ? [row.citation.retrieval_service ?? "serpapi"]
    : []));
  const sourceDisplayName = source !== "google_scholar"
    ? sourceName
    : scholarServices.size > 1
      ? text.scholarViaMixed
      : scholarServices.has("scraperapi")
        ? text.scholarViaScraperApi
        : text.scholarViaSerpApi;
  const summaries = useMemo<Summary[]>(() => conferences.map((conference) => {
    const conferenceRows = sourceRows.filter((row) => row.conference.id === conference.id);
    const counts = conferenceRows.flatMap((row) => row.citation ? [row.citation.total_citations] : []);
    if (!counts.length) return {
      conference,
      award_count: conferenceRows.length,
      cited_paper_count: 0,
      citations: { n: 0 },
    };
    const [min, q1, med, q3, max] = fiveNumber(counts);
    return {
      conference,
      award_count: conferenceRows.length,
      cited_paper_count: counts.length,
      citations: {
        n: counts.length,
        min,
        q1,
        median: med,
        q3,
        max,
        mean: counts.reduce((sum, count) => sum + count, 0) / counts.length,
      },
    };
  }), [conferences, sourceRows]);
  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const visibleRows = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);
  const yearOptions = [...new Set(availableYears.length ? availableYears : [data.year])]
    .sort((a, b) => b - a);
  useEffect(() => setPage(1), [active, metric, source]);
  useEffect(() => {
    if (!citationSources.includes(source)) setSource(initialSource);
  }, [citationSources, initialSource, source]);
  useEffect(() => {
    if (!hasAgeMetric && metric === "c3") setMetric("total");
  }, [hasAgeMetric, metric]);

  const toggle = (id: string) => setActive((current) => {
    const next = new Set(current);
    if (next.has(id) && next.size > 1) next.delete(id); else next.add(id);
    return next;
  });

  return (
    <>
      <section className="hero">
        <div className="hero-copy">
          <p className="kicker">{text.kicker}</p>
          <h1><span>{text.titleLead}</span><em>{text.titleImpact}</em></h1>
          <p className="lede">{text.lede}</p>
        </div>
        <aside className="hero-stat">
          <div><strong>{data.rows.length}</strong><span>{text.papers}</span></div>
          <div><strong>{matched}</strong><span>{text.linked}</span></div>
          <small>{data.year} {text.coverage} · {text.snapshot} {formatDate(data.generated_at, locale)}</small>
        </aside>
      </section>

      <section className="control-bar">
        <div className="control-group"><span>{text.year}</span><label className="year-picker">
          <select value={data.year} onChange={(event) => onYearChange(Number(event.target.value))} aria-label={text.year}>
            {yearOptions.map((year) => <option value={year} key={year}>{year}</option>)}
          </select>
          <svg viewBox="0 0 16 16" aria-hidden="true"><path d="m4 6 4 4 4-4" /></svg>
        </label></div>
        <div className="conference-toggles" aria-label={text.filter}>
          {conferences.map((conference) => <button key={conference.id} className={active.has(conference.id) ? "active" : ""} onClick={() => toggle(conference.id)}><i style={{ background: colors[conference.id] }} />{conference.short_name}</button>)}
        </div>
        {citationSources.length > 1 && <div className="segmented provider-selector" aria-label={text.sourceMetric}>
          {citationSources.map((provider) => <button key={provider} className={source === provider ? "active" : ""} onClick={() => setSource(provider)}>{providerName(provider)}</button>)}
        </div>}
        <div className="segmented" aria-label={text.metric}>
          <button className={metric === "total" ? "active" : ""} onClick={() => setMetric("total")}>{text.current}</button>
          <button disabled={!hasAgeMetric} className={metric === "c3" ? "active" : ""} onClick={() => setMetric("c3")}>{text.firstThree}</button>
        </div>
        <button className="capture-button" onClick={() => window.print()} title={text.captureTitle}>{text.capture}</button>
      </section>
      <aside className="review-banner">
        <span>{text.coverageNote}</span>
        {language === "zh"
          ? `已收录全部 ${data.rows.length} 条官方获奖记录；其中 ${data.rows.length - matched} 篇论文尚无已核验的 ${sourceName} 实体，因此该来源暂不显示引用量。`
          : `All ${data.rows.length} official award records are included; ${data.rows.length - matched} papers do not yet have a verified ${sourceName} entity and are shown without counts from that source.`}
        <a href="#/methodology">{text.verify}</a>
      </aside>

      <ConferenceSummary summaries={summaries} />

      <section className="panel ranking-panel">
        <div className="panel-heading">
          <div><p className="kicker">{text.ranking}</p><h2>{metric === "total" ? text.rankingCurrent : text.rankingWindow}</h2></div>
          <span className="source-pill">{text.source} · {sourceDisplayName}</span>
        </div>
        <div className="ranking-header" aria-hidden="true">
          <span>{text.rank}</span><span>{text.paper}</span><span>{text.topic}</span><span>{text.conference}</span><span>{text.citations}</span>
        </div>
        <div className="ranking-list">
          {visibleRows.map((row, index) => (
            <a className="ranking-row" key={row.paper.id} href={`#/paper/${row.paper.id}?source=${source}&year=${data.year}`} title={row.paper.canonical_title}>
              <span className="rank">{String((page - 1) * PAGE_SIZE + index + 1).padStart(2, "0")}</span>
              <span className="paper-copy"><b>{row.paper.canonical_title}</b><small>{row.paper.authors.slice(0, 3).map((author) => author.name).join(", ")}{row.paper.authors.length > 3 ? " et al." : ""}</small></span>
              <span className="topic-cell" title={topicFor(row) ? text.topicOpenAlex : text.topicUnavailable}>{topicFor(row)?.display_name ?? text.notIndexed}</span>
              <span className="conference-cell"><i style={{ background: colors[row.conference.id] }} />{row.conference.short_name}</span>
              <span className="citation-number">{row.citation ? compactNumber(valueFor(row, metric) ?? 0, locale) : "—"}<small>{row.citation ? `${text.citations.toLowerCase()} · ${providerAbbreviation(row.citation.provider)}` : text.unmatched}</small></span>
            </a>
          ))}
        </div>
        <div className="pagination">
          <span>{text.showing} {(page - 1) * PAGE_SIZE + 1}–{Math.min(page * PAGE_SIZE, filtered.length)} {text.of} {filtered.length}</span>
          <div><button disabled={page === 1} onClick={() => setPage((value) => value - 1)}>← {text.previous}</button><b>{page} / {totalPages}</b><button disabled={page === totalPages} onClick={() => setPage((value) => value + 1)}>{text.next} →</button></div>
        </div>
      </section>

      <section className="panel comparison-panel">
        <div className="panel-heading"><div><p className="kicker">{text.comparison}</p><h2>{text.distributions}</h2></div><span className="source-pill">{metric === "total" ? text.current : text.firstThree}</span></div>
        <ComparisonCharts rows={filtered} metric={metric} />
      </section>
    </>
  );
}
