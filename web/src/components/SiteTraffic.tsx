import { useEffect, useState } from "react";

const SCRIPT_ID = "goatcounter-script";
const SCRIPT_URL = "https://gc.zgo.at/count.v5.js";
const SCRIPT_INTEGRITY = "sha384-atnOLvQb9t+jTSipvd75X2yginT4PjVbqDdlJAmxMm+wYElFmeR6EmLP5bYeoRVQ";

interface GoatCounterApi {
  count: (data?: { path?: string; title?: string }) => void;
}

type GoatCounterWindow = Window & { goatcounter?: GoatCounterApi };

let scriptReady: Promise<void> | null = null;

export function normalizeGoatCounterCode(value: string | undefined): string | null {
  const code = value?.trim().toLowerCase();
  return code && /^[a-z0-9-]+$/.test(code) ? code : null;
}

export function goatCounterTotalUrl(code: string): string {
  return `https://${code}.goatcounter.com/counter/TOTAL.json`;
}

function loadGoatCounter(code: string): Promise<void> {
  if (scriptReady) return scriptReady;
  scriptReady = new Promise((resolve, reject) => {
    const existing = document.getElementById(SCRIPT_ID) as HTMLScriptElement | null;
    if (existing && (window as GoatCounterWindow).goatcounter?.count) {
      resolve();
      return;
    }
    const script = existing ?? document.createElement("script");
    script.id = SCRIPT_ID;
    script.src = SCRIPT_URL;
    script.async = true;
    script.crossOrigin = "anonymous";
    script.integrity = SCRIPT_INTEGRITY;
    script.dataset.goatcounter = `https://${code}.goatcounter.com/count`;
    script.dataset.goatcounterSettings = JSON.stringify({ no_onload: true });
    script.addEventListener("load", () => resolve(), { once: true });
    script.addEventListener("error", () => reject(new Error("GoatCounter failed to load")), { once: true });
    if (!existing) document.head.appendChild(script);
  });
  return scriptReady;
}

function routePath(): string {
  return `${window.location.pathname}${window.location.search}${window.location.hash}`;
}

export function SiteTraffic({ label, title }: { label: string; title: string }) {
  const code = normalizeGoatCounterCode(import.meta.env.VITE_GOATCOUNTER_CODE);
  const [views, setViews] = useState<string | null>(null);

  useEffect(() => {
    if (!code) return;
    let active = true;
    const trackRoute = () => {
      (window as GoatCounterWindow).goatcounter?.count({
        path: routePath(),
        title: document.title,
      });
    };
    loadGoatCounter(code)
      .then(() => {
        if (!active) return;
        trackRoute();
        window.addEventListener("hashchange", trackRoute);
        return fetch(goatCounterTotalUrl(code));
      })
      .then((response) => {
        if (!active || !response?.ok) return;
        return response.json() as Promise<{ count?: string }>;
      })
      .then((payload) => {
        if (active && payload?.count) setViews(payload.count);
      })
      .catch(() => {
        // Analytics and its public counter are optional and must never block the site.
      });
    return () => {
      active = false;
      window.removeEventListener("hashchange", trackRoute);
    };
  }, [code]);

  if (!code) return null;
  return (
    <a className="site-traffic" href="https://www.goatcounter.com/" target="_blank" rel="noreferrer" title={title}>
      <svg viewBox="0 0 20 20" aria-hidden="true"><path d="M2.2 10s2.8-4.2 7.8-4.2 7.8 4.2 7.8 4.2-2.8 4.2-7.8 4.2S2.2 10 2.2 10Z" /><circle cx="10" cy="10" r="2.2" /></svg>
      <span>{label}</span>
      <strong>{views ?? "—"}</strong>
    </a>
  );
}
