import { Link } from "react-router-dom";
import { PageHeader } from "../components/ui/PageHeader";
import { StatCard } from "../components/ui/StatCard";
import { EmptyState } from "../components/ui/EmptyState";
import { formatDateTime, formatMode, formatScore } from "../utils/formatters";
import { getScoreMeaning } from "../utils/scoreInsights";
import { useDashboard } from "../hooks/useDashboard";

export default function DashboardPage() {
  const {
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
  } = useDashboard();

  return (
    <div className="container page-stack">
      <PageHeader
        eyebrow={t("workspace")}
        title={`${t("welcomeBack")}${user?.full_name ? `, ${user.full_name}` : ""}`}
        subtitle={t("launchReviewTrack")}
      />

      {showOnboarding ? (
        <section className="dashboard-grid">
          <div className="panel glass-card">
            <h2>{t("onboardingTitle")}</h2>
            <p className="muted">{t("onboardingSubtitle")}</p>

            <form className="form-grid" onSubmit={handleSaveOnboarding}>
              <div className="form-field">
                <label>{t("targetRole")}</label>
                <input
                  type="text"
                  value={onboarding.targetRole}
                  onChange={(e) => setOnboarding((prev) => ({ ...prev, targetRole: e.target.value }))}
                  placeholder={t("targetRolePlaceholder")}
                />
              </div>

              <div className="form-field">
                <label>{t("confidenceLevel")}</label>
                <select
                  value={onboarding.confidence}
                  onChange={(e) => setOnboarding((prev) => ({ ...prev, confidence: e.target.value }))}
                >
                  <option value="">{t("selectOption")}</option>
                  <option value="low">{t("confidenceLow")}</option>
                  <option value="medium">{t("confidenceMedium")}</option>
                  <option value="high">{t("confidenceHigh")}</option>
                </select>
              </div>

              <div className="form-field">
                <label>{t("focusArea")}</label>
                <select
                  value={onboarding.focusArea}
                  onChange={(e) => setOnboarding((prev) => ({ ...prev, focusArea: e.target.value }))}
                >
                  <option value="">{t("selectOption")}</option>
                  <option value="communication">{t("focusCommunication")}</option>
                  <option value="backend_basics">{t("focusBackendBasics")}</option>
                  <option value="problem_solving">{t("focusProblemSolving")}</option>
                  <option value="projects">{t("focusProjects")}</option>
                </select>
              </div>

              <div className="answer-actions">
                <button className="btn btn-primary" type="submit">
                  {t("saveOnboarding")}
                </button>
                <button className="btn btn-ghost" type="button" onClick={handleSkipOnboarding}>
                  {t("skipForNow")}
                </button>
              </div>
            </form>
          </div>
        </section>
      ) : null}

      <section className="stats-grid">
        <StatCard label={t("totalSessions")} value={stats.total} />
        <StatCard label={t("completed")} value={stats.completed} />
        <StatCard label={t("averageScore")} value={stats.average} hint={t("acrossRecordedSessions")} />
      </section>

      <section className="stats-grid">
        <StatCard
          label={t("currentReadiness")}
          value={stats.readiness?.label || "-"}
          hint={stats.readiness?.readiness || t("notEnoughData")}
        />
        <StatCard label={t("recentTrend")} value={stats.trend} />
        <StatCard label={t("topPracticeMode")} value={stats.dominantMode} />
      </section>

      <section className="dashboard-grid">
        <div className="panel glass-card">
          <h2>{t("createNewSession")}</h2>
          <p className="muted">{t("createSessionSubtitle")}</p>

          <form className="form-grid" onSubmit={handleCreateSession}>
            <div className="form-field">
              <label>{t("track")}</label>
              <select
                value={createForm.track}
                onChange={(e) => setCreateForm((prev) => ({ ...prev, track: e.target.value }))}
              >
                <option value="backend">{t("backend")}</option>
              </select>
            </div>

            <div className="form-field">
              <label>{t("level")}</label>
              <select
                value={createForm.level}
                onChange={(e) => setCreateForm((prev) => ({ ...prev, level: e.target.value }))}
              >
                <option value="junior">{t("junior")}</option>
                <option value="mid">{t("mid")}</option>
                <option value="senior">{t("senior")}</option>
              </select>
            </div>

            <div className="form-field">
              <label>{t("mode")}</label>
              <select
                value={createForm.mode}
                onChange={(e) => setCreateForm((prev) => ({ ...prev, mode: e.target.value }))}
              >
                <option value="standard">{t("standard")}</option>
                <option value="leetcode">{t("leetcode")}</option>
                <option value="project_aware">{t("projectAware")}</option>
              </select>
            </div>

            {createForm.mode === "project_aware" ? (
              <div className="form-field">
                <label>{t("projectFile")}</label>
                <input type="file" onChange={(e) => setSelectedFile(e.target.files?.[0] || null)} />
                <span className="field-hint">{t("uploadHint")}</span>
              </div>
            ) : null}

            {createError ? <div className="alert-error">{createError}</div> : null}

            <button className="btn btn-primary" type="submit" disabled={creatingSession}>
              {creatingSession ? t("preparingSession") : t("createAndStart")}
            </button>
          </form>
        </div>

        <div className="panel glass-card">
          <h2>{t("progressSnapshot")}</h2>

          {!history.length ? (
            <EmptyState title={t("noSessionsYet")} description={t("noSessionsDesc")} />
          ) : (
            <div className="score-breakdown">
              <div className="insight-block">
                <strong>{t("readinessSignal")}</strong>
                <p className="muted">
                  {stats.readiness ? `${stats.readiness.label} - ${stats.readiness.readiness}` : t("notEnoughData")}
                </p>
              </div>

              <div className="insight-block">
                <strong>{t("recentTrend")}</strong>
                <p className="muted">{stats.trend}</p>
              </div>

              <div className="insight-block">
                <strong>{t("topPracticeMode")}</strong>
                <p className="muted">{stats.dominantMode}</p>
              </div>
            </div>
          )}
        </div>
      </section>

      <section className="dashboard-grid">
        <div className="panel glass-card">
          <div className="panel-topline">
            <h2>{t("previousSessions")}</h2>
            <div className="conversation-meta">
              <div className="form-field">
                <input
                  type="text"
                  value={filters.search}
                  onChange={(e) => setFilters((prev) => ({ ...prev, search: e.target.value }))}
                  placeholder={t("searchSessions")}
                />
              </div>

              <div className="form-field">
                <select
                  value={filters.mode}
                  onChange={(e) => setFilters((prev) => ({ ...prev, mode: e.target.value }))}
                >
                  <option value="all">{t("allModes")}</option>
                  <option value="standard">{t("standard")}</option>
                  <option value="leetcode">{t("leetcode")}</option>
                  <option value="project_aware">{t("projectAware")}</option>
                </select>
              </div>

              <div className="form-field">
                <select
                  value={filters.status}
                  onChange={(e) => setFilters((prev) => ({ ...prev, status: e.target.value }))}
                >
                  <option value="all">{t("allStatuses")}</option>
                  <option value="completed">{t("completed")}</option>
                  <option value="in_progress">{t("inProgress")}</option>
                </select>
              </div>
            </div>
          </div>

          {loadingHistory ? (
            <p className="muted">{t("loadingSessions")}</p>
          ) : pageError ? (
            <div className="alert-error">{pageError}</div>
          ) : filteredHistory.length === 0 ? (
            <EmptyState title={t("noMatchingSessions")} description={t("tryDifferentFilters")} />
          ) : (
            <div className="session-list">
              {filteredHistory.map((session) => {
                const meaning = getScoreMeaning(session.average_score || 0, language);

                return (
                  <article key={session.id} className="session-card">
                    <div className="session-card-top">
                      <div>
                        <h3>
                          {session.track} · {formatMode(session.mode)}
                        </h3>
                        <p className="muted">
                          {session.level} · {session.status} · {formatDateTime(session.created_at)}
                        </p>
                      </div>

                      <div className="score-pill">Avg {formatScore(session.average_score)}</div>
                    </div>

                    {session.average_score !== null ? (
                      <p className="session-summary">
                        <strong>{meaning.label}</strong> - {meaning.readiness}
                      </p>
                    ) : null}

                    {session.report_summary ? (
                      <p className="session-summary">{session.report_summary}</p>
                    ) : (
                      <p className="session-summary muted">{t("noReportSummaryYet")}</p>
                    )}

                    <div className="session-actions">
                      <Link className="btn btn-secondary btn-sm" to={`/interview/${session.id}`}>
                        {t("open")}
                      </Link>
                      <Link className="btn btn-ghost btn-sm" to={`/transcript/${session.id}`}>
                        {t("transcriptOnly")}
                      </Link>
                      {session.status === "completed" ? (
                        <Link className="btn btn-ghost btn-sm" to={`/report/${session.id}`}>
                          {t("report")}
                        </Link>
                      ) : null}
                    </div>
                  </article>
                );
              })}
            </div>
          )}
        </div>
      </section>
    </div>
  );
}