import { useEffect, useRef, useState, type ReactNode } from "react";
import { formatDate } from "../data";
import semanticScholarMark from "../assets/semantic-scholar-mark.svg";
import { usePreferences, type ThemePreference } from "../preferences";
import { SiteTraffic } from "./SiteTraffic";

function ThemeIcon({ theme }: { theme: ThemePreference }) {
  if (theme === "dark") {
    return <svg className="theme-icon-dark" viewBox="0 0 20 20" aria-hidden="true"><path d="M15.8 12.7A6.6 6.6 0 0 1 7.3 4.2 6.6 6.6 0 1 0 15.8 12.7Z" /></svg>;
  }
  if (theme === "system") {
    return <svg viewBox="0 0 20 20" aria-hidden="true"><rect x="2.7" y="3.6" width="14.6" height="10.2" rx="1.6" /><path d="M7.2 17h5.6M10 13.8V17" /></svg>;
  }
  return <svg viewBox="0 0 20 20" aria-hidden="true"><circle cx="10" cy="10" r="3.2" /><path d="M10 1.8v2M10 16.2v2M1.8 10h2M16.2 10h2M4.2 4.2l1.4 1.4M14.4 14.4l1.4 1.4M15.8 4.2l-1.4 1.4M5.6 14.4l-1.4 1.4" /></svg>;
}

export function Shell({ children, updatedAt }: { children: ReactNode; updatedAt?: string }) {
  const { language, locale, setLanguage, setTheme, theme } = usePreferences();
  const [themeMenuOpen, setThemeMenuOpen] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const themePicker = useRef<HTMLDivElement>(null);
  const headerActions = useRef<HTMLDivElement>(null);
  const text = language === "zh" ? {
    home: "SecAwardLens 首页",
    rankings: "论文与排名",
    methodology: "方法说明",
    acknowledgements: "致谢",
    theme: "主题",
    light: "亮色",
    dark: "暗色",
    system: "跟随系统",
    language: "语言",
    switchLanguage: "切换为英文",
    data: "引用数据",
    refreshed: "更新于",
    license: "代码采用 Apache-2.0；上游数据遵循各自条款",
    s2: "Semantic Scholar API 支持与署名",
    siteViews: "全站访问量",
    trafficTitle: "由隐私友好的 GoatCounter 提供；公开计数最多延迟 4 小时",
  } : {
    home: "SecAwardLens home",
    rankings: "Papers & rankings",
    methodology: "Methodology",
    acknowledgements: "Acknowledgements",
    theme: "Theme",
    light: "Light",
    dark: "Dark",
    system: "System",
    language: "Language",
    switchLanguage: "切换为中文",
    data: "Citation data",
    refreshed: "refreshed",
    license: "Code Apache-2.0 · Upstream data retains provider terms",
    s2: "Semantic Scholar API support and attribution",
    siteViews: "Site views",
    trafficTitle: "Privacy-friendly statistics by GoatCounter; public counts may lag by up to 4 hours",
  };
  const themes: { id: ThemePreference; label: string }[] = [
    { id: "light", label: text.light },
    { id: "dark", label: text.dark },
    { id: "system", label: text.system },
  ];
  const currentTheme = themes.find((item) => item.id === theme) ?? themes[0];
  useEffect(() => {
    const closeOnOutsideClick = (event: MouseEvent) => {
      if (!themePicker.current?.contains(event.target as Node)) setThemeMenuOpen(false);
      if (!headerActions.current?.contains(event.target as Node)) setMobileMenuOpen(false);
    };
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setThemeMenuOpen(false);
        setMobileMenuOpen(false);
      }
    };
    document.addEventListener("mousedown", closeOnOutsideClick);
    document.addEventListener("keydown", closeOnEscape);
    return () => {
      document.removeEventListener("mousedown", closeOnOutsideClick);
      document.removeEventListener("keydown", closeOnEscape);
    };
  }, []);
  const home = () => { window.location.hash = "/"; };
  const repositoryUrl = (import.meta.env.VITE_REPOSITORY_URL as string | undefined)
    ?? "https://github.com/QGrain/sec-award-lens";
  return (
    <>
      <header className="site-header">
        <button className="brand" onClick={home} aria-label={text.home}>
          <span className="brand-mark" aria-hidden="true"><i /><i /><i /></span>
          <span>SecAward<span>Lens</span></span>
        </button>
        <div className="header-actions" ref={headerActions}>
          <button
            className="mobile-nav-trigger"
            type="button"
            aria-label={language === "zh" ? "打开主导航" : "Open main navigation"}
            aria-haspopup="menu"
            aria-expanded={mobileMenuOpen}
            onClick={() => setMobileMenuOpen((open) => !open)}
          >
            <svg viewBox="0 0 20 20" aria-hidden="true"><path d="M3 5.5h14M3 10h14M3 14.5h14" /></svg>
          </button>
          <nav className={`main-nav${mobileMenuOpen ? " open" : ""}`} aria-label={language === "zh" ? "主导航" : "Main navigation"}>
            <a href="#/" onClick={() => setMobileMenuOpen(false)}>{text.rankings}</a>
            <a href="#/methodology" onClick={() => setMobileMenuOpen(false)}>{text.methodology}</a>
            <a href="#/acknowledgements" onClick={() => setMobileMenuOpen(false)}>{text.acknowledgements}</a>
            <a href={repositoryUrl} target="_blank" rel="noreferrer" onClick={() => setMobileMenuOpen(false)}>GitHub ↗</a>
          </nav>
          <div className="preference-controls">
            <div className="theme-picker" ref={themePicker}>
              <button
                className="preference-button theme-trigger"
                type="button"
                aria-label={`${text.theme}: ${currentTheme.label}`}
                aria-haspopup="menu"
                aria-expanded={themeMenuOpen}
                onClick={() => setThemeMenuOpen((open) => !open)}
              >
                <ThemeIcon theme={theme} />
                <span>{currentTheme.label}</span>
                <svg className="chevron" viewBox="0 0 16 16" aria-hidden="true"><path d="m4 6 4 4 4-4" /></svg>
              </button>
              {themeMenuOpen && <div className="theme-menu" role="menu" aria-label={text.theme}>
                {themes.map((item) => <button
                  type="button"
                  role="menuitemradio"
                  aria-checked={theme === item.id}
                  className={theme === item.id ? "active" : ""}
                  key={item.id}
                  onClick={() => {
                    setTheme(item.id);
                    setThemeMenuOpen(false);
                  }}
                >
                  <ThemeIcon theme={item.id} />
                  <span>{item.label}</span>
                  <i aria-hidden="true">✓</i>
                </button>)}
              </div>}
            </div>
            <button
              className="language-toggle"
              type="button"
              onClick={() => setLanguage(language === "en" ? "zh" : "en")}
              aria-label={text.switchLanguage}
              title={text.switchLanguage}
            >
              <span className={language === "en" ? "active" : ""}>EN</span>
              <i aria-hidden="true" />
              <span className={language === "zh" ? "active" : ""}>中</span>
            </button>
          </div>
        </div>
      </header>
      <main>{children}</main>
      <footer>
        <div className="footer-meta">
          <div className="footer-status"><span className="status-dot" /> {text.data}{updatedAt ? ` · ${text.refreshed} ${formatDate(updatedAt, locale)}` : ""}</div>
          <SiteTraffic label={text.siteViews} title={text.trafficTitle} />
        </div>
        <a className="s2-attribution" href="https://www.semanticscholar.org/?utm_source=api" target="_blank" rel="noreferrer" title={text.s2}>
          <img src={semanticScholarMark} alt="" /><span>Semantic Scholar</span>
        </a>
        <div>{text.license}</div>
      </footer>
    </>
  );
}
