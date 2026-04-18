import { Link } from "react-router-dom";

export default function NotFoundPage() {
  return (
    <div className="container page-stack">
      <div className="panel glass-card centered-card">
        <div className="eyebrow">404</div>
        <h1>Page not found</h1>
        <p className="page-subtitle">
          The page you were looking for does not exist or was moved.
        </p>
        <Link className="btn btn-primary" to="/">
          Back to home
        </Link>
      </div>
    </div>
  );
}