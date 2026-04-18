import { useState } from "react";
import { useForm } from "react-hook-form";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { useAppSettings } from "../hooks/useAppSettings";
import { useT } from "../utils/i18n";
import { getErrorMessage } from "../utils/httpError";

export default function RegisterPage() {
  const { register: registerUser } = useAuth();
  const { language } = useAppSettings();
  const t = useT(language);
  const navigate = useNavigate();

  const [serverError, setServerError] = useState("");
  const [isSubmittingForm, setIsSubmittingForm] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm({
    defaultValues: {
      full_name: "",
      email: "",
      password: "",
    },
  });

  const onSubmit = async (values) => {
    setServerError("");
    setIsSubmittingForm(true);

    try {
      await registerUser(values);
      navigate("/login");
    } catch (error) {
      setServerError(getErrorMessage(error, "Registration failed."));
    } finally {
      setIsSubmittingForm(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-card glass-card">
        <div className="eyebrow">{t("createAccount")}</div>
        <h1>{t("getStartedTitle")}</h1>
        <p className="page-subtitle">{t("registerSubtitle")}</p>

        <form className="form-grid" onSubmit={handleSubmit(onSubmit)}>
          <div className="form-field">
            <label>{t("fullName")}</label>
            <input type="text" placeholder="Demo User" {...register("full_name")} />
          </div>

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
              placeholder="Minimum 6 characters"
              {...register("password", {
                required: "Password is required",
                minLength: { value: 6, message: "Minimum 6 characters" },
              })}
            />
            {errors.password ? (
              <span className="field-error">{errors.password.message}</span>
            ) : null}
          </div>

          {serverError ? <div className="alert-error">{serverError}</div> : null}

          <button className="btn btn-primary" type="submit" disabled={isSubmittingForm}>
            {isSubmittingForm ? "Creating account..." : t("createAccount")}
          </button>
        </form>

        <p className="auth-footer">
          {t("alreadyRegistered")} <Link to="/login">{t("login")}</Link>
        </p>
      </div>
    </div>
  );
}