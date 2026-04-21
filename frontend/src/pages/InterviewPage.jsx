import { Link } from "react-router-dom";
import { PageHeader } from "../components/ui/PageHeader";
import { formatDateTime, formatMode, formatScore } from "../utils/formatters";
import { formatDuration, getCategoryLabel } from "../utils/scoreInsights";
import { useInterview } from "../hooks/useInterview";

export default function InterviewPage() {
  const {
    t,
    sessionId,
    language,
    session,
    transcript,
    scoreSummary,
    reviewMap,
    lastAnswerReview,
    answer,
    setAnswer,
    loadingPage,
    submittingAnswer,
    finishingInterview,
    pageError,
    actionError,
    lastAnswerScore,
    elapsedSeconds,
    answerTimings,
    conversationEndRef,
    latestInterviewerMessage,
    averageResponseTime,
    scoreMeaning,
    topStrengthAreas,
    focusAreas,
    handleSubmitAnswer,
    handleFinishInterview,
  } = useInterview();

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
              transcript.map((message) => {
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
              <div className="muted">{t("draftAutosaved")}</div>
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

          {lastAnswerReview ? (
            <div className="panel glass-card">
              <h3>{t("latestAnswerReview")}</h3>
              <div className={`readiness-card readiness-${lastAnswerReview.tone}`}>
                <div className="readiness-top">
                  <strong>{t("answerReview")}</strong>
                  <span>{formatScore(lastAnswerReview.overall_score)}</span>
                </div>
                <p>{lastAnswerReview.summary}</p>

                <div className="insight-block">
                  <strong>{t("whatWorked")}</strong>
                  <ul className="insight-list">
                    {lastAnswerReview.what_worked.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                </div>

                <div className="insight-block">
                  <strong>{t("improveNext")}</strong>
                  <ul className="insight-list">
                    {lastAnswerReview.improve_next.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                </div>

                <p className="muted">{lastAnswerReview.encouragement}</p>
              </div>
            </div>
          ) : null}

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
        </aside>
      </section>
    </div>
  );
}