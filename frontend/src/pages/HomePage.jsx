import { Link } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { useAppSettings } from "../hooks/useAppSettings";
import { useT } from "../utils/i18n";

export default function HomePage() {
  const { isAuthenticated } = useAuth();
  const { language } = useAppSettings();
  const t = useT(language);

  return (
    <div className="landing">
      <section className="hero-section">
        <div className="container hero-grid">
          <div className="hero-copy">
            <div className="eyebrow">Interview practice that feels modern</div>
            <h1>
              Replace confusing prep tools with one clear, premium interview workspace.
            </h1>
            <p className="hero-text">
              Practice realistic backend interviews, coding-style rounds, and project-aware
              sessions based on your own files. Clean UI, focused workflow, and room to
              grow into a serious product.
            </p>

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
              <span className="badge-soft">Standard</span>
              <span className="badge-soft">LeetCode Mode</span>
              <span className="badge-soft">Project Aware</span>
              <span className="badge-soft">Reports & Progress</span>
            </div>
          </div>

          <div className="hero-panel glass-card">
            <div className="hero-panel-top">
              <span className="status-dot" />
              <span>Mock interview in progress</span>
            </div>

            <div className="chat-preview">
              <div className="chat-bubble interviewer">
                Explain the difference between authentication and authorization.
              </div>
              <div className="chat-bubble candidate">
                Authentication verifies identity. Authorization decides what the user is
                allowed to access.
              </div>
              <div className="chat-bubble interviewer">
                Good. How would JWT validation fit into a backend middleware chain?
              </div>
            </div>

            <div className="hero-stats">
              <div>
                <strong>3</strong>
                <span>Interview modes</span>
              </div>
              <div>
                <strong>Full</strong>
                <span>Transcript support</span>
              </div>
              <div>
                <strong>Live</strong>
                <span>Score feedback</span>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}