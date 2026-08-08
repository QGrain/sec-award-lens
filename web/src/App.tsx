import { lazy, Suspense, useEffect, useState } from "react";
import { Shell } from "./components/Shell";
import { loadIndex, loadYear } from "./data";
import { usePreferences } from "./preferences";
import type { IndexData, Provider, YearData } from "./types";

const Methodology = lazy(() => import("./pages/Methodology").then((module) => ({ default: module.Methodology })));
const Acknowledgements = lazy(() => import("./pages/Acknowledgements").then((module) => ({ default: module.Acknowledgements })));
const Overview = lazy(() => import("./pages/Overview").then((module) => ({ default: module.Overview })));
const PaperDetail = lazy(() => import("./pages/PaperDetail").then((module) => ({ default: module.PaperDetail })));

function useRoute() {
  const [hash, setHash] = useState(window.location.hash || "#/");
  useEffect(() => {
    const listener = () => setHash(window.location.hash || "#/");
    window.addEventListener("hashchange", listener);
    return () => window.removeEventListener("hashchange", listener);
  }, []);
  const [path, query = ""] = hash.slice(1).split("?");
  const requestedYear = Number(new URLSearchParams(query).get("year"));
  const source = new URLSearchParams(query).get("source");
  const requestedSource = (["google_scholar", "openalex", "semantic_scholar"] as const)
    .includes(source as Provider) ? source as Provider : null;
  return {
    path: path || "/",
    requestedYear: Number.isInteger(requestedYear) && requestedYear > 0 ? requestedYear : null,
    requestedSource,
  };
}

export default function App() {
  const { language } = usePreferences();
  const text = language === "zh" ? {
    notFound: "页面不存在",
    returnToRankings: "返回论文排名",
    unable: "无法加载数据",
    loadingRecords: "正在加载已核验记录…",
    loadingView: "正在加载页面…",
  } : {
    notFound: "Page not found",
    returnToRankings: "Return to rankings",
    unable: "Unable to load data",
    loadingRecords: "Loading verified records…",
    loadingView: "Loading view…",
  };
  const { path: route, requestedYear, requestedSource } = useRoute();
  const [index, setIndex] = useState<IndexData | null>(null);
  const [year, setYear] = useState<YearData | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    loadIndex().then(setIndex).catch((reason: Error) => setError(reason.message));
  }, []);
  const selectedYear = index
    ? (requestedYear !== null && index.years.includes(requestedYear)
      ? requestedYear
      : index.default_year)
    : null;
  useEffect(() => {
    if (!index || route !== "/" || selectedYear === null || year?.year === selectedYear) return;
    let cancelled = false;
    setYear(null);
    setError("");
    loadYear(selectedYear)
      .then((data) => { if (!cancelled) setYear(data); })
      .catch((reason: Error) => { if (!cancelled) setError(reason.message); });
    return () => { cancelled = true; };
  }, [index, route, selectedYear, year?.year]);
  let content;
  if (route === "/methodology") content = <Methodology years={index?.years} />;
  else if (route === "/acknowledgements") content = <Acknowledgements />;
  else if (route.startsWith("/paper/")) content = <PaperDetail id={decodeURIComponent(route.slice(7))} initialSource={requestedSource ?? index?.preferred_citation_source} />;
  else if (route !== "/") content = <section className="empty-state"><h1>{text.notFound}</h1><a href="#/">{text.returnToRankings}</a></section>;
  else if (error) content = <section className="empty-state"><h1>{text.unable}</h1><p>{error}</p></section>;
  else if (!index || !year || year.year !== selectedYear) content = <div className="loading">{text.loadingRecords}</div>;
  else content = <Overview
    data={year}
    conferences={index.conferences}
    citationSources={index.citation_sources}
    preferredCitationSource={index.preferred_citation_source}
    initialCitationSource={requestedSource}
    availableYears={index.years}
    onYearChange={(nextYear) => { window.location.hash = `/?year=${nextYear}`; }}
  />;
  return <Shell updatedAt={index?.generated_at}><Suspense fallback={<div className="loading">{text.loadingView}</div>}>{content}</Suspense></Shell>;
}
