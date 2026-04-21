import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { useAppSettings } from "../hooks/useAppSettings";
import { useT } from "../utils/i18n";
import { PageHeader } from "../components/ui/PageHeader";
import { interviewService } from "../services/interviewService";
import { sessionService } from "../services/sessionService";
import { formatDateTime, formatScore } from "../utils/formatters";
import { getErrorMessage } from "../utils/httpError";
import {
  getBottomCategories,
  getCategoryLabel,
  getScoreMeaning,
  getTopCategories,
} from "../utils/scoreInsights";

export default function TranscriptPage() {
  const { sessionId } = useParams();
  const { token } = useAuth();
  const { language } = useAppSettings();
  const t = useT(language);

  const [transcript, setTranscript] = useState(null);
  const [scoreSummary, setScoreSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [pageError, setPageError] = useState("");

  useEffect(() => {
    const run = async () => {
      setLoading(true);
      setPageError("");

      try {
        const [transcriptData, scoreData] = await Promise.all([
          interviewService.getTranscript(token, sessionId),
          sessionService.getScoreSummary(token, sessionId).catch(() => null),
        ]);

        setTranscript(transcriptData);
        setScoreSummary(scoreData);
      } catch (error) {
        setPageError(getErrorMessage(error, "Failed to load transcript."));
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
    return getTopCategories(scoreSummary?.breakdown || [], language, 2);
  }, [scoreSummary, language]);

  const focusAreas = useMemo(() => {
    return getBottomCategories(scoreSummary?.breakdown || [], language, 2);
  }, [scoreSummary, language]);

  const reviewMap = useMemo(() => {
    return Object.fromEntries((transcript?.answer_reviews || []).map((item) => [item.message_id, item]));
  }, [transcript]);

  return (
    <div className="container page-stack">
      <PageHeader
        eyebrow={t("transcript")}
        title={`Session #${sessionId}`}
        subtitle={t("fullConversationHistory")}
        actions={
          <div className="inline-actions">
            <Link className="btn btn-ghost btn-sm" to={`/report/${sessionId}`}>
              {t("report")}
            </Link>
          </div>
        }
      />

      {loading ? (
        <div className="panel glass-card">
          <p className="muted">{t("loadingTranscript")}</p>
        </div>
      ) : pageError ? (
        <div className="panel glass-card">
          <div className="alert-error">{pageError}</div>
        </div>
      ) : (
        <div className="report-layout">
          <section className="panel glass-card">
            <div className="conversation-feed">
              {transcript?.messages?.length ? (
                transcript.messages.map((message) => {
                  const review = message.role === "candidate" ? reviewMap[message.id] : null;

                  return (
                    <div key={message.id} className={`message-row ${message.role}`}>
                      <div className="message-meta">
                        <span className={`role-badge ${message.role}`}>{message.role}</span>
                        <span>{formatDateTime(message.created_at)}</span>
                      </div>
                      <div className="message-card">{message.content}</div>

                      {review ? (
                        <div className={`readiness-card readiness-${review.tone}`} style={{ marginTop: 10 }}>
                          <div className="readiness-top">
                            <strong>{t("answerReview")}</strong>
                            <span>{formatScore(review.overall_score)}</span>
                          </div>
                          <p>{review.summary}</p>

                          <div className="insight-block">
                            <strong>{t("whatWorked")}</strong>
                            <ul className="insight-list">
                              {review.what_worked.map((item) => (
                                <li key={item}>{item}</li>
                              ))}
                            </ul>
                          </div>

                          <div className="insight-block">
                            <strong>{t("improveNext")}</strong>
                            <ul className="insight-list">
                              {review.improve_next.map((item) => (
                                <li key={item}>{item}</li>
                              ))}
                            </ul>
                          </div>

                          <p className="muted">{review.encouragement}</p>
                        </div>
                      ) : null}
                    </div>
                  );
                })
              ) : (
                <p className="muted">{t("noTranscriptYet")}</p>
              )}
            </div>
          </section>

          <aside className="panel glass-card">
            <h3>{t("sessionInsights")}</h3>

            {!scoreSummary ? (
              <p className="muted">{t("noScoreDataYet")}</p>
            ) : (
              <div className="score-breakdown">
                <div className={`readiness-card readiness-${scoreMeaning.tone}`}>
                  <div className="readiness-top">
                    <strong>{scoreMeaning.label}</strong>
                    <span>{formatScore(scoreSummary.average_score)}</span>
                  </div>
                  <div className="muted">{scoreMeaning.readiness}</div>
                  <p>{scoreMeaning.explanation}</p>
                </div>

                <div className="score-breakdown-header">
                  <strong>{t("scoreSummary")}</strong>
                  <span>
                    {scoreSummary.total_scores} {t("scoreRows")}
                  </span>
                </div>

                {scoreSummary.breakdown?.map((item) => (
                  <div key={item.category} className="score-row">
                    <span>{getCategoryLabel(item.category, language)}</span>
                    <strong>{formatScore(item.score)}</strong>
                  </div>
                ))}

                <div className="insight-block">
                  <strong>{t("excellentNow")}</strong>
                  <ul className="insight-list">
                    {topStrengthAreas.length
                      ? topStrengthAreas.map((item) => <li key={item}>{item}</li>)
                      : scoreMeaning.strengths.map((item) => <li key={item}>{item}</li>)}
                  </ul>
                </div>

                <div className="insight-block">
                  <strong>{t("improveNow")}</strong>
                  <ul className="insight-list">
                    {focusAreas.length
                      ? focusAreas.map((item) => <li key={item}>{item}</li>)
                      : scoreMeaning.improvements.map((item) => <li key={item}>{item}</li>)}
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