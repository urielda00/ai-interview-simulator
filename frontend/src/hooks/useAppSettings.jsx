import { createContext, useContext, useEffect, useMemo, useState } from "react";

const APP_SETTINGS_KEY = "ai_interview_app_settings";

const defaultSettings = {
  language: "en",
};

const AppSettingsContext = createContext(null);

export function AppSettingsProvider({ children }) {
  const [settings, setSettings] = useState(() => {
    const raw = localStorage.getItem(APP_SETTINGS_KEY);
    if (!raw) return defaultSettings;

    try {
      return { ...defaultSettings, ...JSON.parse(raw) };
    } catch {
      return defaultSettings;
    }
  });

  useEffect(() => {
    localStorage.setItem(APP_SETTINGS_KEY, JSON.stringify(settings));

    const lang = settings.language || "en";
    const dir = lang === "he" ? "rtl" : "ltr";

    document.documentElement.lang = lang;
    document.documentElement.dir = dir;
    document.body.setAttribute("data-language", lang);
    document.body.setAttribute("data-dir", dir);
  }, [settings]);

  const value = useMemo(() => {
    const language = settings.language || "en";
    const isHebrew = language === "he";
    const direction = isHebrew ? "rtl" : "ltr";

    return {
      language,
      isHebrew,
      direction,
      setLanguage: (nextLanguage) =>
        setSettings((prev) => ({
          ...prev,
          language: nextLanguage,
        })),
      toggleLanguage: () =>
        setSettings((prev) => ({
          ...prev,
          language: prev.language === "he" ? "en" : "he",
        })),
    };
  }, [settings]);

  return <AppSettingsContext.Provider value={value}>{children}</AppSettingsContext.Provider>;
}

export function useAppSettings() {
  const context = useContext(AppSettingsContext);

  if (!context) {
    throw new Error("useAppSettings must be used within AppSettingsProvider");
  }

  return context;
}