import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

export type Language = "en" | "zh";
export type ThemePreference = "light" | "dark" | "system";
export type ResolvedTheme = "light" | "dark";

interface Preferences {
  language: Language;
  locale: "en-US" | "zh-CN";
  resolvedTheme: ResolvedTheme;
  setLanguage: (language: Language) => void;
  setTheme: (theme: ThemePreference) => void;
  theme: ThemePreference;
}

const PreferencesContext = createContext<Preferences | null>(null);
const LANGUAGE_KEY = "secawardlens-language";
const THEME_KEY = "secawardlens-theme";

function storedLanguage(): Language {
  try {
    return localStorage.getItem(LANGUAGE_KEY) === "zh" ? "zh" : "en";
  } catch {
    return "en";
  }
}

function storedTheme(): ThemePreference {
  try {
    const value = localStorage.getItem(THEME_KEY);
    return value === "dark" || value === "system" ? value : "light";
  } catch {
    return "light";
  }
}

function store(key: string, value: string) {
  try {
    localStorage.setItem(key, value);
  } catch {
    // Preferences remain available for this tab when storage is unavailable.
  }
}

function systemTheme(): ResolvedTheme {
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

export function PreferencesProvider({ children }: { children: ReactNode }) {
  const [language, setLanguageState] = useState<Language>(storedLanguage);
  const [theme, setThemeState] = useState<ThemePreference>(storedTheme);
  const [system, setSystem] = useState<ResolvedTheme>(systemTheme);
  const resolvedTheme = theme === "system" ? system : theme;

  useEffect(() => {
    const media = window.matchMedia("(prefers-color-scheme: dark)");
    const update = () => setSystem(media.matches ? "dark" : "light");
    media.addEventListener("change", update);
    return () => media.removeEventListener("change", update);
  }, []);

  useEffect(() => {
    document.documentElement.dataset.theme = resolvedTheme;
    document.documentElement.lang = language === "zh" ? "zh-CN" : "en";
    document.documentElement.style.colorScheme = resolvedTheme;
    document.querySelector('meta[name="theme-color"]')?.setAttribute(
      "content",
      resolvedTheme === "dark" ? "#0e1815" : "#f3f6f1",
    );
    document.title = language === "zh"
      ? "SecAwardLens — 安全顶会获奖论文引用影响力"
      : "SecAwardLens — Citation Impact of Award-Winning Security Papers";
  }, [language, resolvedTheme]);

  const value = useMemo<Preferences>(() => ({
    language,
    locale: language === "zh" ? "zh-CN" : "en-US",
    resolvedTheme,
    setLanguage: (next) => {
      store(LANGUAGE_KEY, next);
      setLanguageState(next);
    },
    setTheme: (next) => {
      store(THEME_KEY, next);
      setThemeState(next);
    },
    theme,
  }), [language, resolvedTheme, theme]);

  return <PreferencesContext.Provider value={value}>{children}</PreferencesContext.Provider>;
}

export function usePreferences() {
  const value = useContext(PreferencesContext);
  if (!value) throw new Error("usePreferences must be used inside PreferencesProvider");
  return value;
}
