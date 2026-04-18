import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { useAppSettings } from "../hooks/useAppSettings";
import { useT } from "../utils/i18n";
import { PageHeader } from "../components/ui/PageHeader";
import { interviewService } from "../services/interviewService";
import { formatDateTime } from "../utils/formatters";
import { getErrorMessage } from "../utils/httpError";

export default function TranscriptPage() {
  const { sessionId } = useParams();
  const { token } = useAuth();
  const { language } = useAppSettings();
  const t = useT(language);

  const [transcript, setTranscript] = useState(null);
  const [loading, setLoading] = useState(true);
  const [pageError, setPageError] = useState("");

  useEffect(() => {
    const run = async () => {
      setLoading(true);
      setPageError("");

      try {
        const data = await interviewService.getTranscript(token, sessionId);
        setTranscript(data);
      } catch (error) {
        setPageError(getErrorMessage(error, "Failed to load transcript."));
      } finally {
        setLoading(false);
      }
    };

    run();
  }, [token, sessionId]);

  return (
    <div className="container page-stack">
      <PageHeader
        eyebrow={t("transcript")}
        title={`Session #${sessionId}`}
        subtitle={t("fullConversationHistory")}
      />

      <div className="panel glass-card">
        {loading ? (
          <p className="muted">{t("loadingTranscript")}</p>
        ) : pageError ? (
          <div className="alert-error">{pageError}</div>
        ) : (
          <div className="conversation-feed">
            {transcript?.messages?.length ? (
              transcript.messages.map((message) => (
                <div key={message.id} className={`message-row ${message.role}`}>
                  <div className="message-meta">
                    <span className={`role-badge ${message.role}`}>{message.role}</span>
                    <span>{formatDateTime(message.created_at)}</span>
                  </div>
                  <div className="message-card">{message.content}</div>
                </div>
              ))
            ) : (
              <p className="muted">{t("noTranscriptYet")}</p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}