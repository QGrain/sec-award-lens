import type { IndexData, PaperData, YearData } from "./types";

const base = import.meta.env.BASE_URL.replace(/\/$/, "");

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(`${base}/data/${path}`, { cache: "no-store" });
  if (!response.ok) throw new Error(`Data request failed (${response.status})`);
  return response.json() as Promise<T>;
}

export const loadIndex = () => getJson<IndexData>("index.json");
export const loadYear = (year: number) => getJson<YearData>(`years/${year}.json`);
export const loadPaper = (id: string) => getJson<PaperData>(`papers/${id}.json`);

export const formatDate = (iso: string, locale = "en-US") =>
  new Intl.DateTimeFormat(locale, { year: "numeric", month: "short", day: "numeric" }).format(
    new Date(iso),
  );

export const compactNumber = (value: number, locale = "en-US") =>
  new Intl.NumberFormat(locale, { notation: value >= 1000 ? "compact" : "standard" }).format(value);
