import { useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { useAppSettings } from "../hooks/useAppSettings";
import { useT } from "../utils/i18n";
import { PageHeader } from "../components/ui/PageHeader";
import { reportService } from "../services/reportService";
import { sessionService } from "../services/sessionService";
import { formatDateTime, formatScore } from "../utils/formatters";
import { getErrorMessage } from "../utils/httpError";
import { getCategoryLabel, getScoreMeaning } from "../utils/scoreInsights";

export default function ReportPage() {
  const { sessionId } = useParams();
  const { token } = useAuth();
  const { language } = useAppSettings();
  const t = useT(language);

  const [report, setReport] = useState(null);
  const [scoreSummary, setScoreSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [pageError, setPageError] = useState("");

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
    return getScoreMeaning(scoreSummary?.average_score || 0);
  }, [scoreSummary]);

  return (
    <div className="container page-stack">
      <PageHeader
        eyebrow={t("finalReport")}
        title={`Session #${sessionId}`}
        subtitle="Strengths, weaknesses, readiness, and a focused study plan."
      />

      {loading ? (
        <p className="muted">{t("loadingReport")}</p>
      ) : pageError ? (
        <div className="alert-error">{pageError}</div>
      ) : !report ? (
        <div className="panel glass-card">
          <p className="muted">{t("reportUnavailable")}</p>
        </div>
      ) : (
        <div className="report-layout">
          <section className="panel glass-card">
            {scoreSummary ? (
              <div className={`readiness-card readiness-${scoreMeaning.tone} report-readiness-card`}>
                <div className="readiness-top">
                  <strong>{scoreMeaning.label}</strong>
                  <span>{formatScore(scoreSummary.average_score)}</span>
                </div>
                <div className="muted">{scoreMeaning.readiness}</div>
                <p>{scoreMeaning.explanation}</p>
              </div>
            ) : null}

            <div className="report-block">
              <h3>{t("summary")}</h3>
              <p>{report?.summary}</p>
            </div>

            <div className="report-block">
              <h3>{t("strengths")}</h3>
              <p>{report?.strengths}</p>
            </div>

            <div className="report-block">
              <h3>{t("weaknesses")}</h3>
              <p>{report?.weaknesses}</p>
            </div>

            <div className="report-block">
              <h3>{t("studyPlan")}</h3>
              <p>{report?.study_plan}</p>
            </div>

            <div className="report-meta muted">
              Report created: {formatDateTime(report?.created_at)}
            </div>
          </section>

          <aside className="panel glass-card">
            <h3>{t("scoreInsights")}</h3>

            {!scoreSummary ? (
              <p className="muted">No score breakdown available.</p>
            ) : (
              <div className="score-breakdown">
                <div className="score-breakdown-header">
                  <strong>{t("scoreSummary")}</strong>
                  <span>{scoreSummary.total_scores} score rows</span>
                </div>

                {scoreSummary.breakdown.map((item) => (
                  <div className="score-row" key={item.category}>
                    <span>{getCategoryLabel(item.category)}</span>
                    <strong>{formatScore(item.score)}</strong>
                  </div>
                ))}

                <div className="insight-block">
                  <strong>{t("excellentNow")}</strong>
                  <ul className="insight-list">
                    {scoreMeaning.strengths.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                </div>

                <div className="insight-block">
                  <strong>{t("improveNow")}</strong>
                  <ul className="insight-list">
                    {scoreMeaning.improvements.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                </div>
              </div>
            )}
          </aside>
        </div>
      )}
    </div>
  );
}