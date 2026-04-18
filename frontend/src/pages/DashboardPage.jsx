import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { useAppSettings } from "../hooks/useAppSettings";
import { useT } from "../utils/i18n";
import { PageHeader } from "../components/ui/PageHeader";
import { StatCard } from "../components/ui/StatCard";
import { EmptyState } from "../components/ui/EmptyState";
import { sessionService } from "../services/sessionService";
import { interviewService } from "../services/interviewService";
import { uploadService } from "../services/uploadService";
import { formatDateTime, formatMode, formatScore } from "../utils/formatters";
import { getErrorMessage } from "../utils/httpError";

const defaultForm = {
  track: "backend",
  level: "junior",
  mode: "standard",
};

export default function DashboardPage() {
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

  const stats = useMemo(() => {
    const completed = history.filter((item) => item.status === "completed").length;
    const average =
      history.length > 0
        ? (
            history.reduce((sum, item) => sum + Number(item.average_score || 0), 0) / history.length
          ).toFixed(1)
        : "-";

    return {
      total: history.length,
      completed,
      average,
    };
  }, [history]);

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

  return (
    <div className="container page-stack">
      <PageHeader
        eyebrow={t("workspace")}
        title={`${t("welcomeBack")}${user?.full_name ? `, ${user.full_name}` : ""}`}
        subtitle={t("launchReviewTrack")}
      />

      <section className="stats-grid">
        <StatCard label={t("totalSessions")} value={stats.total} />
        <StatCard label={t("completed")} value={stats.completed} />
        <StatCard label={t("averageScore")} value={stats.average} hint={t("acrossRecordedSessions")} />
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
          <h2>{t("previousSessions")}</h2>

          {loadingHistory ? (
            <p className="muted">{t("loadingSessions")}</p>
          ) : pageError ? (
            <div className="alert-error">{pageError}</div>
          ) : history.length === 0 ? (
            <EmptyState title={t("noSessionsYet")} description={t("noSessionsDesc")} />
          ) : (
            <div className="session-list">
              {history.map((session) => (
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
              ))}
            </div>
          )}
        </div>
      </section>
    </div>
  );
}