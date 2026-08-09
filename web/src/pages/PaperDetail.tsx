import { useEffect, useMemo, useState } from "react";
import type { EChartsCoreOption } from "echarts/core";
import { Chart } from "../components/Chart";
import { compactNumber, formatDate, loadPaper, providerName } from "../data";
import { usePreferences } from "../preferences";
import type { PaperData, Provider } from "../types";

export function PaperDetail({ id, initialSource }: { id: string; initialSource?: Provider | null }) {
  const { language, locale, resolvedTheme } = usePreferences();
  const text = language === "zh" ? {
    notFound: "未找到论文",
    returnToRankings: "返回论文排名",
    loading: "正在加载论文记录…",
    allPapers: "返回全部论文",
    affiliations: "作者与机构",
    affiliationNote: "机构信息由 OpenAlex 提供，可能并不完整。",
    topic: "OpenAlex 主题",
    official: "论文官方页面",
    current: "当前引用",
    snapshot: "快照",
    noEntity: "暂无已核验的引用数据实体",
    firstThree: "发表后三年",
    ageWindow: "固定发表年龄窗口",
    unavailable: "该来源暂无逐年引用数据",
    entityMatch: "实体匹配",
    pending: "待核验",
    requires: "需要人工核验",
    profile: "引用概况",
    byYear: "按引用论文发表年份统计",
    noYear: "该快照没有提供逐年引用量。",
    noYearScholar: "当前基线复用了首次检索结果，因此没有逐年引用量；下次由 SerpApi 按固定论文 ID 刷新后可生成该图。",
    noYearFallback: "当前快照经由 HTML 代理获取，只包含引用总量，不包含逐年引用量。",
    chartNote: "这里的年份是引用论文的发表年份，并非引用计数器在当年的历史快照值。",
    yearSeriesSnapshot: "逐年分布快照",
    audit: "审计记录",
    trustworthy: "为何这条记录值得信任",
    awardSource: "奖项来源",
    officialConference: "会议官方页面",
    rawAward: "原始奖项名称",
    matchDecision: "匹配决定",
    confidence: "置信度",
    citationSource: "引用来源",
    notResolved: "尚未解析",
    snapshotHistory: "快照历史",
    observations: "条不可变观测",
    reviewNote: "核验备注",
    chartAria: "引用论文按发表年份分布",
    source: "引用来源",
    viaSerpApi: "经由 SerpApi 获取",
    viaScraperApi: "经由 ScraperAPI 获取",
  } : {
    notFound: "Paper not found",
    returnToRankings: "Return to rankings",
    loading: "Loading paper record…",
    allPapers: "All papers",
    affiliations: "Authors and affiliations",
    affiliationNote: "Affiliations are supplied by OpenAlex and may be incomplete.",
    topic: "OpenAlex topic",
    official: "Official paper",
    current: "Current citations",
    snapshot: "snapshot",
    noEntity: "No verified citation entity",
    firstThree: "First 3 years",
    ageWindow: "publication-age window",
    unavailable: "Year-level counts unavailable from this source",
    entityMatch: "Entity match",
    pending: "pending",
    requires: "requires review",
    profile: "Citation profile",
    byYear: "Citations by citing year",
    noYear: "This snapshot does not provide year-level citation counts.",
    noYearScholar: "The current baseline reused the discovery result, which has no yearly series. A pinned-ID refresh through SerpApi can populate this chart.",
    noYearFallback: "This HTML-proxy snapshot provides the current total, but not a citing-year series.",
    chartNote: "This is the citing works’ publication year—not a historical snapshot of what the counter displayed then.",
    yearSeriesSnapshot: "Year distribution snapshot",
    audit: "Audit trail",
    trustworthy: "Why this record is trustworthy",
    awardSource: "Award source",
    officialConference: "Official conference page",
    rawAward: "Raw award label",
    matchDecision: "Match decision",
    confidence: "confidence",
    citationSource: "Citation source",
    notResolved: "not resolved",
    snapshotHistory: "Snapshot history",
    observations: "immutable observation(s)",
    reviewNote: "Review note",
    chartAria: "Citations received by publication year of citing works",
    source: "Citation source",
    viaSerpApi: "retrieved via SerpApi",
    viaScraperApi: "retrieved via ScraperAPI",
  };
  const [data, setData] = useState<PaperData | null>(null);
  const [error, setError] = useState("");
  const [selectedSource, setSelectedSource] = useState<Provider | null>(null);
  useEffect(() => { loadPaper(id).then(setData).catch((reason: Error) => setError(reason.message)); }, [id]);
  const availableProviders = data
    ? (["google_scholar", "openalex", "semantic_scholar"] as Provider[])
      .filter((item) => Boolean(data.citation_history[item]?.length))
    : [];
  const provider = selectedSource && availableProviders.includes(selectedSource)
    ? selectedSource
    : initialSource && availableProviders.includes(initialSource)
      ? initialSource
      : availableProviders[0] ?? null;
  const latest = provider ? data?.citation_history[provider]?.at(-1) : undefined;
  const latestWithYearCounts = provider
    ? data?.citation_history[provider]?.slice().reverse()
      .find((item) => item.citations_by_citing_year.length > 0)
    : undefined;
  const dark = resolvedTheme === "dark";
  const yearlyOption = useMemo<EChartsCoreOption>(() => ({
    grid: { left: 45, right: 15, top: 18, bottom: 42 },
    tooltip: { trigger: "axis", backgroundColor: dark ? "#172a24" : "#fff", borderColor: dark ? "#42574f" : "#d5dfd8", textStyle: { color: dark ? "#edf5f1" : "#152a24" } },
    xAxis: { type: "category", data: latestWithYearCounts?.citations_by_citing_year.map((item) => item.year) ?? [], axisTick: { show: false }, axisLabel: { color: dark ? "#a9bcb5" : "#53655f" } },
    yAxis: { type: "value", minInterval: 1, axisLabel: { color: dark ? "#a9bcb5" : "#53655f" }, splitLine: { lineStyle: { color: dark ? "#344740" : "#dce5df" } } },
    series: [{ type: "bar", data: latestWithYearCounts?.citations_by_citing_year.map((item) => item.count) ?? [], itemStyle: { color: "#45d6ad", borderRadius: [4, 4, 0, 0] }, barMaxWidth: 42 }],
  }), [dark, latestWithYearCounts]);
  if (error) return <section className="empty-state"><h1>{text.notFound}</h1><p>{error}</p><a href="#/">{text.returnToRankings}</a></section>;
  if (!data) return <div className="loading">{text.loading}</div>;
  const doi = data.paper.identifiers.find((item) => item.scheme === "doi");
  const awardYear = Number(data.awards[0]?.edition_id.slice(-4)) || data.paper.publication_year;
  const binding = data.bindings.find((item) => item.provider === provider)
    ?? data.bindings.find((item) => item.provider === "openalex");
  const affiliations = new Map(
    data.enrichment?.authors.map((author) => [
      author.author_name,
      [...new Set(author.affiliations.map((item) => item.display_name))],
    ]) ?? [],
  );
  const hasAffiliations = [...affiliations.values()].some((items) => items.length);
  const hasYearCounts = Boolean(latestWithYearCounts);
  const noYearMessage = provider === "google_scholar"
    ? latest?.retrieval_service === "serpapi" ? text.noYearScholar : text.noYearFallback
    : text.noYear;
  const citationProviderName = provider ? providerName(provider) : text.source;
  const providerObservationName = provider === "google_scholar"
    ? `${citationProviderName} · ${latest?.retrieval_service === "scraperapi" ? text.viaScraperApi : text.viaSerpApi}`
    : citationProviderName;
  const matchStatus = binding
    ? language === "zh"
      ? ({
          pending: "待核验",
          candidate: "候选",
          auto_verified: "自动核验",
          manually_verified: "人工核验",
          rejected: "已拒绝",
          stale: "已过期",
        } as Record<string, string>)[binding.status] ?? binding.status
      : binding.status.replace("_", " ")
    : text.pending;
  const matchMethod = binding?.method
    ? language === "zh"
      ? ({
          doi_exact: "DOI 精确匹配",
          title_exact: "标题精确匹配",
          fuzzy_review: "模糊匹配待复核",
          manual_override: "人工确认",
        } as Record<string, string>)[binding.method] ?? binding.method
      : binding.method.replace("_", " ")
    : text.requires;
  const providerUrl = binding?.external_id
    ? provider === "google_scholar"
      ? `https://scholar.google.com/scholar?cites=${binding.external_id}`
      : provider === "semantic_scholar"
      ? `https://www.semanticscholar.org/paper/${binding.external_id}?utm_source=api`
      : `https://openalex.org/${binding.external_id}`
    : null;
  const chooseProvider = (next: Provider) => {
    setSelectedSource(next);
    window.location.hash = `/paper/${encodeURIComponent(id)}?source=${next}&year=${awardYear}`;
  };
  return (
    <>
      <section className="paper-hero">
        <a href={`#/?year=${awardYear}${provider ? `&source=${provider}` : ""}`} className="back-link">← {language === "zh" ? `${awardYear} 年${text.allPapers}` : `${text.allPapers} · ${awardYear}`}</a>
        <div className="paper-venue-line">
          <strong>{data.paper.venue_name}</strong>
          <span>{data.awards[0]?.raw_award_name}</span>
        </div>
        <h1>{data.paper.canonical_title}</h1>
        <p className="authors" aria-label={text.affiliations}>
          {data.paper.authors.map((author, index) => {
            const institutions = affiliations.get(author.name) ?? [];
            return <span key={author.name}><b>{author.name}</b>{institutions.length ? <small> ({institutions.join(", ")})</small> : null}{index < data.paper.authors.length - 1 ? ", " : ""}</span>;
          })}
        </p>
        {hasAffiliations && <small className="affiliation-note">{text.affiliationNote}</small>}
        {data.enrichment?.primary_topic && <p className="paper-topic"><span>{text.topic}</span>{data.enrichment.primary_topic.display_name}</p>}
        <div className="paper-links">
          {data.paper.official_paper_url && <a href={data.paper.official_paper_url} target="_blank" rel="noreferrer">{text.official} ↗</a>}
          {doi && <a href={`https://doi.org/${doi.value}`} target="_blank" rel="noreferrer">DOI ↗</a>}
          {providerUrl && <a href={providerUrl} target="_blank" rel="noreferrer">{citationProviderName} ↗</a>}
        </div>
      </section>
      {availableProviders.length > 1 && <nav className="detail-provider-switch" aria-label={text.source}>
        <span>{text.source}</span>
        <div className="segmented provider-selector">
          {availableProviders.map((item) => <button key={item} className={provider === item ? "active" : ""} onClick={() => chooseProvider(item)}>{providerName(item)}</button>)}
        </div>
      </nav>}
      <section className="paper-metrics">
        <article><span>{text.current}</span><strong>{latest ? compactNumber(latest.total_citations, locale) : "—"}</strong><small>{latest ? `${providerObservationName} · ${text.snapshot} ${formatDate(latest.retrieved_at, locale)}` : text.noEntity}</small></article>
        <article><span>{text.firstThree}</span><strong>{hasYearCounts ? latestWithYearCounts?.citations_by_citing_year.filter((item) => item.year >= data.paper.publication_year && item.year < data.paper.publication_year + 3).reduce((sum, item) => sum + item.count, 0) : "—"}</strong><small>{hasYearCounts ? text.ageWindow : text.unavailable}</small></article>
        <article><span>{text.entityMatch}</span><strong className="match-status">{matchStatus}</strong><small>{matchMethod}</small></article>
      </section>
      <section className="paper-grid">
        <article className="panel">
          <div className="panel-heading"><div><p className="kicker">{text.profile}</p><h2>{text.byYear}</h2></div></div>
          {hasYearCounts ? <Chart option={yearlyOption} height={320} label={text.chartAria} /> : <p className="empty-chart">{noYearMessage}</p>}
          <p className="chart-note">{text.chartNote}{latestWithYearCounts ? ` ${text.yearSeriesSnapshot}: ${formatDate(latestWithYearCounts.retrieved_at, locale)}.` : ""}</p>
        </article>
        <aside className="provenance-card">
          <p className="kicker">{text.audit}</p><h2>{text.trustworthy}</h2>
          <dl>
            <div><dt>{text.awardSource}</dt><dd><a href={data.awards[0]?.official_source.url} target="_blank" rel="noreferrer">{text.officialConference} ↗</a></dd></div>
            <div><dt>{text.rawAward}</dt><dd>{data.awards[0]?.raw_award_name}</dd></div>
            <div><dt>{text.matchDecision}</dt><dd>{matchStatus}{binding?.confidence != null ? ` · ${Math.round(binding.confidence * 100)}% ${text.confidence}` : ` · ${text.requires}`}</dd></div>
            <div><dt>{text.citationSource}</dt><dd>{providerObservationName} {binding?.external_id ?? text.notResolved}</dd></div>
            <div><dt>{text.snapshotHistory}</dt><dd>{provider ? data.citation_history[provider]?.length ?? 0 : 0} {text.observations}</dd></div>
            {binding?.review_notes && <div><dt>{text.reviewNote}</dt><dd>{binding.review_notes}</dd></div>}
          </dl>
        </aside>
      </section>
    </>
  );
}
