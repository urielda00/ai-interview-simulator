import { PageHeader } from "../components/ui/PageHeader";
import { formatDateTime, formatScore } from "../utils/formatters";
import { getCategoryLabel } from "../utils/scoreInsights";
import { useReport } from "../hooks/useReport";

export default function ReportPage() {
  const {
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
  } = useReport();

  return (
    <div className="container page-stack">
      <PageHeader
        eyebrow={t("finalReport")}
        title={`Session #${sessionId}`}
        subtitle={t("strengthsWeaknessesPlan")}
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

            {topStrengthAreas.length ? (
              <div className="report-block">
                <h3>{t("topStrengthAreas")}</h3>
                <ul className="insight-list">
                  {topStrengthAreas.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </div>
            ) : null}

            {focusAreas.length ? (
              <div className="report-block">
                <h3>{t("focusAreas")}</h3>
                <ul className="insight-list">
                  {focusAreas.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
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
              {t("reportCreated")}: {formatDateTime(report?.created_at)}
            </div>
          </section>

          <aside className="panel glass-card">
            <h3>{t("scoreInsights")}</h3>

            {!scoreSummary ? (
              <p className="muted">{t("noScoreBreakdownAvailable")}</p>
            ) : (
              <div className="score-breakdown">
                <div className="score-breakdown-header">
                  <strong>{t("scoreSummary")}</strong>
                  <span>
                    {scoreSummary.total_scores} {t("scoreRows")}
                  </span>
                </div>

                {scoreSummary.breakdown.map((item) => (
                  <div className="score-row" key={item.category}>
                    <span>{getCategoryLabel(item.category, language)}</span>
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