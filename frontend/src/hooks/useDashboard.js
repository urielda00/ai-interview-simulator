import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "./useAuth";
import { useAppSettings } from "./useAppSettings";
import { useT } from "../utils/i18n";
import { sessionService } from "../services/sessionService";
import { interviewService } from "../services/interviewService";
import { uploadService } from "../services/uploadService";
import { getErrorMessage } from "../utils/httpError";
import { formatMode } from "../utils/formatters";
import { getDominantMode, getScoreMeaning, getTrendLabel } from "../utils/scoreInsights";

const defaultForm = {
  track: "backend",
  level: "junior",
  mode: "standard",
};

const defaultOnboarding = {
  targetRole: "",
  confidence: "",
  focusArea: "",
};

const defaultFilters = {
  search: "",
  mode: "all",
  status: "all",
};

const ONBOARDING_STORAGE_KEY = "ai_interview_onboarding_v1";

export function useDashboard() {
  const { token, user } = useAuth();
  const { language } = useAppSettings();
  const t = useT(language);
  const navigate = useNavigate();

  const [createForm, setCreateForm] = useState(defaultForm);
  const [selectedFile, setSelectedFile] = useState(null);
  const [history, setHistory] = useState([]);
  const [loadingHistory, setLoadingHistory] = useState(true);
  const [creatingSession, setCreatingSession] = useState(false);
  const [pageError, setPageError] = useState("");
  const [createError, setCreateError] = useState("");

  const [showOnboarding, setShowOnboarding] = useState(() => {
    return !localStorage.getItem(ONBOARDING_STORAGE_KEY);
  });
  const [onboarding, setOnboarding] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem(ONBOARDING_STORAGE_KEY)) || defaultOnboarding;
    } catch {
      return defaultOnboarding;
    }
  });

  const [filters, setFilters] = useState(defaultFilters);

  const loadHistory = async () => {
    setLoadingHistory(true);
    setPageError("");

    try {
      const data = await sessionService.getHistorySessions(token);
      setHistory(data);
    } catch (error) {
      setPageError(getErrorMessage(error, "Failed to load dashboard data."));
    } finally {
      setLoadingHistory(false);
    }
  };

  useEffect(() => {
    loadHistory();
  }, [token]);

  const filteredHistory = useMemo(() => {
    return history.filter((item) => {
      const search = filters.search.trim().toLowerCase();

      const matchesSearch =
        !search ||
        item.track?.toLowerCase().includes(search) ||
        item.level?.toLowerCase().includes(search) ||
        item.mode?.toLowerCase().includes(search) ||
        item.status?.toLowerCase().includes(search) ||
        item.report_summary?.toLowerCase().includes(search);

      const matchesMode = filters.mode === "all" || item.mode === filters.mode;
      const matchesStatus = filters.status === "all" || item.status === filters.status;

      return matchesSearch && matchesMode && matchesStatus;
    });
  }, [history, filters]);

  const stats = useMemo(() => {
    const completedSessions = history.filter((item) => item.status === "completed");
    const completed = completedSessions.length;

    const average =
      completed > 0
        ? (
            completedSessions.reduce((sum, item) => sum + Number(item.average_score || 0), 0) / completed
          ).toFixed(1)
        : "-";

    const latestCompleted = completedSessions[0] || null;
    const previousCompleted = completedSessions[1] || null;
    const latestScore = latestCompleted?.average_score ?? null;

    return {
      total: history.length,
      completed,
      average,
      latestScore,
      readiness: latestScore !== null ? getScoreMeaning(latestScore, language) : null,
      trend:
        latestCompleted && previousCompleted
          ? getTrendLabel(latestCompleted.average_score, previousCompleted.average_score, language)
          : t("notEnoughData"),
      dominantMode: history.length ? formatMode(getDominantMode(history, language)) : t("notEnoughData"),
    };
  }, [history, language, t]);

  const handleCreateSession = async (event) => {
    event.preventDefault();
    setCreateError("");
    setCreatingSession(true);

    try {
      const session = await sessionService.createSession(token, {
        ...createForm,
        language,
      });

      if (createForm.mode === "project_aware" && selectedFile) {
        await uploadService.uploadProjectFile(token, session.id, selectedFile);
      }

      await interviewService.startInterview(token, session.id);
      navigate(`/interview/${session.id}`);
    } catch (error) {
      setCreateError(getErrorMessage(error, "Failed to create session."));
    } finally {
      setCreatingSession(false);
    }
  };

  const handleSaveOnboarding = (event) => {
    event.preventDefault();
    localStorage.setItem(ONBOARDING_STORAGE_KEY, JSON.stringify(onboarding));
    setShowOnboarding(false);
  };

  const handleSkipOnboarding = () => {
    localStorage.setItem(ONBOARDING_STORAGE_KEY, JSON.stringify(onboarding));
    setShowOnboarding(false);
  };

  return {
    t,
    user,
    language,
    createForm,
    setCreateForm,
    setSelectedFile,
    history,
    filteredHistory,
    loadingHistory,
    creatingSession,
    pageError,
    createError,
    stats,
    handleCreateSession,
    showOnboarding,
    onboarding,
    setOnboarding,
    handleSaveOnboarding,
    handleSkipOnboarding,
    filters,
    setFilters,
  };
}