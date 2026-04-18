import { useEffect, useMemo, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { useAppSettings } from "../hooks/useAppSettings";
import { useT } from "../utils/i18n";
import { PageHeader } from "../components/ui/PageHeader";
import { sessionService } from "../services/sessionService";
import { interviewService } from "../services/interviewService";
import { formatDateTime, formatMode, formatScore } from "../utils/formatters";
import { getErrorMessage } from "../utils/httpError";
import { formatDuration, getCategoryLabel, getScoreMeaning } from "../utils/scoreInsights";

const ANSWER_TIMING_KEY_PREFIX = "ai_interview_answer_timing_";

export default function InterviewPage() {
  const { sessionId } = useParams();
  const { token } = useAuth();
  const { language } = useAppSettings();
  const t = useT(language);

  const [session, setSession] = useState(null);
  const [transcript, setTranscript] = useState([]);
  const [scoreSummary, setScoreSummary] = useState(null);
  const [answer, setAnswer] = useState("");
  const [loadingPage, setLoadingPage] = useState(true);
  const [submittingAnswer, setSubmittingAnswer] = useState(false);
  const [finishingInterview, setFinishingInterview] = useState(false);
  const [pageError, setPageError] = useState("");
  const [actionError, setActionError] = useState("");
  const [lastAnswerScore, setLastAnswerScore] = useState(null);
  const [questionStartedAt, setQuestionStartedAt] = useState(Date.now());
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [answerTimings, setAnswerTimings] = useState(() => {
    const raw = localStorage.getItem(`${ANSWER_TIMING_KEY_PREFIX}${sessionId}`);
    if (!raw) return [];
    try {
      return JSON.parse(raw);
    } catch {
      return [];
    }
  });

  const conversationEndRef = useRef(null);

  const persistTimings = (next) => {
    setAnswerTimings(next);
    localStorage.setItem(`${ANSWER_TIMING_KEY_PREFIX}${sessionId}`, JSON.stringify(next));
  };

  const loadData = async () => {
    setLoadingPage(true);
    setPageError("");

    try {
      const [sessionData, transcriptData] = await Promise.all([
        sessionService.getSessionById(token, sessionId),
        interviewService.getTranscript(token, sessionId).catch(() => null),
      ]);

      setSession(sessionData);
      setTranscript(transcriptData?.messages || []);

      try {
        const scores = await sessionService.getScoreSummary(token, sessionId);
        setScoreSummary(scores);
      } catch {
        setScoreSummary(null);
      }
    } catch (error) {
      setPageError(getErrorMessage(error, "Failed to load interview."));
    } finally {
      setLoadingPage(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [token, sessionId]);

  useEffect(() => {
    const timer = setInterval(() => {
      setElapsedSeconds(Math.floor((Date.now() - questionStartedAt) / 1000));
    }, 1000);

    return () => clearInterval(timer);
  }, [questionStartedAt]);

  useEffect(() => {
    conversationEndRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [transcript]);

  const latestInterviewerMessage = useMemo(() => {
    const interviewerMessages = transcript.filter((item) => item.role === "interviewer");
    return interviewerMessages[interviewerMessages.length - 1] || null;
  }, [transcript]);

  const averageResponseTime = useMemo(() => {
    if (!answerTimings.length) return 0;
    return answerTimings.reduce((sum, item) => sum + Number(item.seconds || 0), 0) / answerTimings.length;
  }, [answerTimings]);

  const scoreMeaning = useMemo(() => {
    return getScoreMeaning(scoreSummary?.average_score || lastAnswerScore || 0, language);
  }, [scoreSummary, lastAnswerScore, language]);

  const handleSubmitAnswer = async (event) => {
    event.preventDefault();

    if (!answer.trim()) return;

    setSubmittingAnswer(true);
    setActionError("");

    const responseSeconds = Math.floor((Date.now() - questionStartedAt) / 1000);

    try {
      const data = await interviewService.answerInterview(token, {
        session_id: Number(sessionId),
        answer: answer.trim(),
      });

      setLastAnswerScore(data.score);

      const nextTimingRow = {
        questionIndex: transcript.filter((item) => item.role === "candidate").length + 1,
        seconds: responseSeconds,
        answeredAt: new Date().toISOString(),
      };

      persistTimings([...answerTimings, nextTimingRow]);
      setAnswer("");
      setQuestionStartedAt(Date.now());
      await loadData();
    } catch (error) {
      setActionError(getErrorMessage(error, "Failed to submit answer."));
    } finally {
      setSubmittingAnswer(false);
    }
  };

  const handleFinishInterview = async () => {
    setFinishingInterview(true);
    setActionError("");

    try {
      await interviewService.finishInterview(token, sessionId);
      await loadData();
    } catch (error) {
      setActionError(getErrorMessage(error, "Failed to finish interview."));
    } finally {
      setFinishingInterview(false);
    }
  };

  if (loadingPage) {
    return (
      <div className="container page-stack">
        <p className="muted">{t("loadingInterview")}</p>
      </div>
    );
  }

  if (pageError) {
    return (
      <div className="container page-stack">
        <div className="alert-error">{pageError}</div>
      </div>
    );
  }

  return (
    <div className="container page-stack">
      <PageHeader
        eyebrow={t("interviewRoom")}
        title={`${session?.track} · ${formatMode(session?.mode)}`}
        subtitle={`${t("level")}: ${session?.level} · ${t("status")}: ${session?.status} · ${t("createdAt")} ${formatDateTime(
          session?.created_at
        )}`}
        actions={
          <div className="inline-actions">
            <Link className="btn btn-ghost btn-sm" to={`/transcript/${sessionId}`}>
              {t("fullTranscript")}
            </Link>
            {session?.status === "completed" ? (
              <Link className="btn btn-ghost btn-sm" to={`/report/${sessionId}`}>
                {t("report")}
              </Link>
            ) : null}
          </div>
        }
      />

      <section className="interview-layout">
        <div className="panel glass-card">
          <div className="panel-topline">
            <h2>{t("conversation")}</h2>
            <div className="conversation-meta">
              {lastAnswerScore !== null ? (
                <div className="score-pill">
                  {t("lastScore")} {formatScore(lastAnswerScore)}
                </div>
              ) : null}
              <div className="score-pill">
                {t("responseTime")}: {formatDuration(elapsedSeconds, language)}
              </div>
            </div>
          </div>

          <div className="conversation-feed conversation-scroll-area">
            {transcript.length === 0 ? (
              <p className="muted">{t("noTranscriptYet")}</p>
            ) : (
              transcript.map((message) => (
                <div key={message.id} className={`message-row ${message.role}`}>
                  <div className="message-meta">
                    <span className={`role-badge ${message.role}`}>{message.role}</span>
                    <span>{formatDateTime(message.created_at)}</span>
                  </div>
                  <div className="message-card">{message.content}</div>
                </div>
              ))
            )}
            <div ref={conversationEndRef} />
          </div>

          {session?.status !== "completed" ? (
            <form className="answer-box" onSubmit={handleSubmitAnswer}>
              <label>{t("yourAnswer")}</label>
              <textarea
                rows={6}
                placeholder={t("typeAnswerPlaceholder")}
                value={answer}
                onChange={(e) => setAnswer(e.target.value)}
              />
              {actionError ? <div className="alert-error">{actionError}</div> : null}
              <div className="answer-actions">
                <button className="btn btn-primary" type="submit" disabled={submittingAnswer}>
                  {submittingAnswer ? t("submitting") : t("sendAnswer")}
                </button>
                <button
                  className="btn btn-secondary"
                  type="button"
                  onClick={handleFinishInterview}
                  disabled={finishingInterview}
                >
                  {finishingInterview ? t("finishing") : t("finishNow")}
                </button>
              </div>
            </form>
          ) : (
            <div className="interview-complete-box">
              <h3>{t("interviewCompleted")}</h3>
              <p className="muted">{t("interviewClosed")}</p>
            </div>
          )}
        </div>

        <aside className="side-column">
          <div className="panel glass-card">
            <h3>{t("currentPrompt")}</h3>
            <p>{latestInterviewerMessage?.content || t("noInterviewerMessageYet")}</p>
          </div>

          <div className="panel glass-card">
            <h3>{t("scoreSummary")}</h3>
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
                  <strong>{t("scoreMeaning")}</strong>
                  <span>
                    {scoreSummary.total_scores} {t("scoreRows")}
                  </span>
                </div>

                {scoreSummary.breakdown.map((item) => (
                  <div key={item.category} className="score-row">
                    <span>{getCategoryLabel(item.category, language)}</span>
                    <strong>{formatScore(item.score)}</strong>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="panel glass-card">
            <h3>{t("sessionTiming")}</h3>
            <div className="timing-stack">
              <div className="score-row">
                <span>{t("averageResponseTime")}</span>
                <strong>{formatDuration(averageResponseTime, language)}</strong>
              </div>

              {answerTimings.map((item) => (
                <div key={`${item.questionIndex}-${item.answeredAt}`} className="score-row">
                  <span>
                    {t("answerTiming")} #{item.questionIndex}
                  </span>
                  <strong>{formatDuration(item.seconds, language)}</strong>
                </div>
              ))}
            </div>
          </div>

          <div className="panel glass-card">
            <h3>{t("sessionInsights")}</h3>

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
        </aside>
      </section>
    </div>
  );
}