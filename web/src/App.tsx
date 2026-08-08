import { lazy, Suspense, useEffect, useState } from "react";
import { Shell } from "./components/Shell";
import { loadIndex, loadYear } from "./data";
import type { IndexData, YearData } from "./types";

const Methodology = lazy(() => import("./pages/Methodology").then((module) => ({ default: module.Methodology })));
const Overview = lazy(() => import("./pages/Overview").then((module) => ({ default: module.Overview })));
const PaperDetail = lazy(() => import("./pages/PaperDetail").then((module) => ({ default: module.PaperDetail })));

function useRoute() {
  const [hash, setHash] = useState(window.location.hash || "#/");
  useEffect(() => {
    const listener = () => setHash(window.location.hash || "#/");
    window.addEventListener("hashchange", listener);
    return () => window.removeEventListener("hashchange", listener);
  }, []);
  return hash.slice(1).split("?")[0];
}

export default function App() {
  const route = useRoute();
  const [index, setIndex] = useState<IndexData | null>(null);
  const [year, setYear] = useState<YearData | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    loadIndex().then(setIndex).catch((reason: Error) => setError(reason.message));
  }, []);
  useEffect(() => {
    if (index && route === "/" && !year) {
      loadYear(index.default_year)
        .then(setYear)
        .catch((reason: Error) => setError(reason.message));
    }
  }, [index, route, year]);
  let content;
  if (route === "/methodology") content = <Methodology />;
  else if (route.startsWith("/paper/")) content = <PaperDetail id={decodeURIComponent(route.slice(7))} />;
  else if (route !== "/") content = <section className="empty-state"><h1>Page not found</h1><a href="#/">Return to rankings</a></section>;
  else if (error) content = <section className="empty-state"><h1>Unable to load data</h1><p>{error}</p></section>;
  else if (!index || !year) content = <div className="loading">Loading verified records…</div>;
  else content = <Overview data={year} conferences={index.conferences} />;
  return <Shell updatedAt={index?.generated_at}><Suspense fallback={<div className="loading">Loading view…</div>}>{content}</Suspense></Shell>;
}
