import { useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { useAuth } from "./useAuth";
import { useAppSettings } from "./useAppSettings";
import { useT } from "../utils/i18n";
import { reportService } from "../services/reportService";
import { sessionService } from "../services/sessionService";
import { getErrorMessage } from "../utils/httpError";
import {
  getBottomCategories,
  getScoreMeaning,
  getTopCategories,
} from "../utils/scoreInsights";

export function useReport() {
  const { sessionId } = useParams();
  const { token } = useAuth();
  const { language } = useAppSettings();
  const t = useT(language);

  const [report, setReport] = useState(null);
  const [scoreSummary, setScoreSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [pageError, setPageError] = useState("");

  // Fetch report and score data concurrently
  useEffect(() => {
    const run = async () => {
      setLoading(true);
      setPageError("");

      try {
        const [reportData, scoreData] = await Promise.all([
          reportService.getReport(token, sessionId),
          sessionService.getScoreSummary(token, sessionId).catch(() => null),
        ]);

        setReport(reportData);
        setScoreSummary(scoreData);
      } catch (error) {
        setPageError(getErrorMessage(error, "Failed to load report."));
      } finally {
        setLoading(false);
      }
    };

    run();
  }, [token, sessionId]);

  const scoreMeaning = useMemo(() => {
    return getScoreMeaning(scoreSummary?.average_score || 0, language);
  }, [scoreSummary, language]);

  const topStrengthAreas = useMemo(() => {
    return getTopCategories(scoreSummary?.breakdown || [], language, 3);
  }, [scoreSummary, language]);

  const focusAreas = useMemo(() => {
    return getBottomCategories(scoreSummary?.breakdown || [], language, 3);
  }, [scoreSummary, language]);

  return {
    t,
    sessionId,
    language,
    report,
    scoreSummary,
    loading,
    pageError,
    scoreMeaning,
    topStrengthAreas,
    focusAreas,
  };
}