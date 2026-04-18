import { Link, NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../../hooks/useAuth";
import { useAppSettings } from "../../hooks/useAppSettings";
import { useT } from "../../utils/i18n";

export function AppShell() {
  const { isAuthenticated, user, logout } = useAuth();
  const { language, toggleLanguage, direction } = useAppSettings();
  const t = useT(language);
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/");
  };

  return (
    <div className={`app-shell ${direction}`}>
      <header className="topbar">
        <div className="container topbar-inner">
          <Link to={isAuthenticated ? "/dashboard" : "/"} className="brand">
            <span className="brand-mark">AI</span>
            <span className="brand-text">{t("brand")}</span>
          </Link>

          <nav className="topnav">
            <button className="btn btn-ghost btn-sm" onClick={toggleLanguage} type="button">
              {t("language")}
            </button>

            <NavLink to={isAuthenticated ? "/dashboard" : "/"} className="nav-link">
              {isAuthenticated ? t("dashboard") : t("home")}
            </NavLink>

            {isAuthenticated ? (
              <>
                <button className="btn btn-secondary btn-sm" onClick={handleLogout}>
                  {t("logout")}
                </button>
                <div className="user-pill">
                  <span className="user-pill-label">{t("signedInAs")}</span>
                  <strong>{user?.full_name || user?.email}</strong>
                </div>
              </>
            ) : (
              <>
                <NavLink to="/login" className="nav-link">
                  {t("login")}
                </NavLink>
                <NavLink to="/register" className="btn btn-primary btn-sm">
                  {t("getStarted")}
                </NavLink>
              </>
            )}
          </nav>
        </div>
      </header>

      <main className="page-main">
        <Outlet />
      </main>
    </div>
  );
}