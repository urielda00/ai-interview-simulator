import { Link } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { useAppSettings } from "../hooks/useAppSettings";
import { useT } from "../utils/i18n";

export default function HomePage() {
  const { isAuthenticated } = useAuth();
  const { language, direction } = useAppSettings();
  const t = useT(language);

  return (
    <div className="landing">
      <section className="hero-section">
        <div className="container hero-grid">
          <div className="hero-copy">
            <div className="eyebrow">{t("homeEyebrow")}</div>
            <h1>{t("homeTitle")}</h1>
            <p className="hero-text">{t("homeDescription")}</p>

            <div className="hero-actions">
              {isAuthenticated ? (
                <Link to="/dashboard" className="btn btn-primary">
                  {t("dashboard")}
                </Link>
              ) : (
                <>
                  <Link to="/register" className="btn btn-primary">
                    {t("startFree")}
                  </Link>
                  <Link to="/login" className="btn btn-secondary">
                    {t("alreadyHaveAccount")}
                  </Link>
                </>
              )}
            </div>

            <div className="hero-badges">
              <span className="badge-soft">{t("standard")}</span>
              <span className="badge-soft">{t("leetcode")}</span>
              <span className="badge-soft">{t("projectAware")}</span>
              <span className="badge-soft">{t("scoreSummary")}</span>
            </div>
          </div>

          <div className="hero-panel glass-card">
            <div className="hero-panel-top">
              <span className="status-dot" />
              <span>{t("mockInterviewInProgress")}</span>
            </div>

            <div className="chat-preview">
              <div className="chat-bubble interviewer" dir={direction}>
                {t("heroQuestion1")}
              </div>
              <div className="chat-bubble candidate" dir={direction}>
                {t("heroAnswer1")}
              </div>
              <div className="chat-bubble interviewer" dir={direction}>
                {t("heroQuestion2")}
              </div>
            </div>

            <div className="hero-stats">
              <div>
                <strong>3</strong>
                <span>{t("interviewModes")}</span>
              </div>
              <div>
                <strong>Full</strong>
                <span>{t("transcriptSupport")}</span>
              </div>
              <div>
                <strong>Live</strong>
                <span>{t("liveScoreFeedback")}</span>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}