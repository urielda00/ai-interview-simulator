import { useState } from "react";
import { useForm } from "react-hook-form";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { useAppSettings } from "../hooks/useAppSettings";
import { useT } from "../utils/i18n";
import { getErrorMessage } from "../utils/httpError";

export default function LoginPage() {
  const { login } = useAuth();
  const { language } = useAppSettings();
  const t = useT(language);
  const navigate = useNavigate();
  const location = useLocation();
  const from = location.state?.from?.pathname || "/dashboard";

  const [serverError, setServerError] = useState("");
  const [isSubmittingForm, setIsSubmittingForm] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm({
    defaultValues: {
      email: "",
      password: "",
    },
  });

  const onSubmit = async (values) => {
    setServerError("");
    setIsSubmittingForm(true);

    try {
      await login(values);
      navigate(from, { replace: true });
    } catch (error) {
      setServerError(getErrorMessage(error, "Login failed."));
    } finally {
      setIsSubmittingForm(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-card glass-card">
        <div className="eyebrow">{t("welcomeBack")}</div>
        <h1>{t("login")}</h1>
        <p className="page-subtitle">{t("signInSubtitle")}</p>

        <form className="form-grid" onSubmit={handleSubmit(onSubmit)}>
          <div className="form-field">
            <label>{t("email")}</label>
            <input
              type="email"
              placeholder="demo@example.com"
              {...register("email", { required: "Email is required" })}
            />
            {errors.email ? <span className="field-error">{errors.email.message}</span> : null}
          </div>

          <div className="form-field">
            <label>{t("password")}</label>
            <input
              type="password"
              placeholder="******"
              {...register("password", { required: "Password is required" })}
            />
            {errors.password ? (
              <span className="field-error">{errors.password.message}</span>
            ) : null}
          </div>

          {serverError ? <div className="alert-error">{serverError}</div> : null}

          <button className="btn btn-primary" type="submit" disabled={isSubmittingForm}>
            {isSubmittingForm ? "Signing in..." : t("login")}
          </button>
        </form>

        <p className="auth-footer">
          {t("noAccountYet")} <Link to="/register">{t("createAccount")}</Link>
        </p>
      </div>
    </div>
  );
}