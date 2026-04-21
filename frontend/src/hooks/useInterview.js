import { useEffect, useMemo, useRef, useState } from "react";
import { useParams } from "react-router-dom";
import { useAuth } from "./useAuth";
import { useAppSettings } from "./useAppSettings";
import { useT } from "../utils/i18n";
import { sessionService } from "../services/sessionService";
import { interviewService } from "../services/interviewService";
import { getErrorMessage } from "../utils/httpError";
import {
  getBottomCategories,
  getScoreMeaning,
  getTopCategories,
} from "../utils/scoreInsights";

const ANSWER_TIMING_KEY_PREFIX = "ai_interview_answer_timing_";
const ANSWER_DRAFT_KEY_PREFIX = "ai_interview_answer_draft_";

export function useInterview() {
  const { sessionId } = useParams();
  const { token } = useAuth();
  const { language } = useAppSettings();
  const t = useT(language);

  const [session, setSession] = useState(null);
  const [transcript, setTranscript] = useState([]);
  const [scoreSummary, setScoreSummary] = useState(null);
  const [answerReviews, setAnswerReviews] = useState([]);
  const [lastAnswerReview, setLastAnswerReview] = useState(null);
  const [answer, setAnswer] = useState(() => localStorage.getItem(`${ANSWER_DRAFT_KEY_PREFIX}${sessionId}`) || "");
  const [loadingPage, setLoadingPage] = useState(true);
  const [submittingAnswer, setSubmittingAnswer] = useState(false);
  const [finishingInterview, setFinishingInterview] = useState(false);
  const [pageError, setPageError] = useState("");
  const [actionError, setActionError] = useState("");
  const [lastAnswerScore, setLastAnswerScore] = useState(null);
  const [questionStartedAt, setQuestionStartedAt] = useState(Date.now());
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [answerTimings, setAnswerTimings] = useState(() => {
    const raw = localStorage.getItem(`${ANSWER_TIMING_KEY_PREFIX}${sessionId}`);
    if (!raw) return [];
    try {
      return JSON.parse(raw);
    } catch {
      return [];
    }
  });

  const conversationEndRef = useRef(null);

  const persistTimings = (next) => {
    setAnswerTimings(next);
    localStorage.setItem(`${ANSWER_TIMING_KEY_PREFIX}${sessionId}`, JSON.stringify(next));
  };

  const loadData = async () => {
    setLoadingPage(true);
    setPageError("");

    try {
      const [sessionData, transcriptData] = await Promise.all([
        sessionService.getSessionById(token, sessionId),
        interviewService.getTranscript(token, sessionId).catch(() => null),
      ]);

      setSession(sessionData);
      setTranscript(transcriptData?.messages || []);
      setAnswerReviews(transcriptData?.answer_reviews || []);

      try {
        const scores = await sessionService.getScoreSummary(token, sessionId);
        setScoreSummary(scores);
      } catch {
        setScoreSummary(null);
      }
    } catch (error) {
      setPageError(getErrorMessage(error, "Failed to load interview."));
    } finally {
      setLoadingPage(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [token, sessionId]);

  useEffect(() => {
    const timer = setInterval(() => {
      setElapsedSeconds(Math.floor((Date.now() - questionStartedAt) / 1000));
    }, 1000);

    return () => clearInterval(timer);
  }, [questionStartedAt]);

  useEffect(() => {
    conversationEndRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [transcript]);

  useEffect(() => {
    localStorage.setItem(`${ANSWER_DRAFT_KEY_PREFIX}${sessionId}`, answer);
  }, [answer, sessionId]);

  const reviewMap = useMemo(() => {
    return Object.fromEntries(answerReviews.map((item) => [item.message_id, item]));
  }, [answerReviews]);

  const latestInterviewerMessage = useMemo(() => {
    const interviewerMessages = transcript.filter((item) => item.role === "interviewer");
    return interviewerMessages[interviewerMessages.length - 1] || null;
  }, [transcript]);

  const averageResponseTime = useMemo(() => {
    if (!answerTimings.length) return 0;
    return answerTimings.reduce((sum, item) => sum + Number(item.seconds || 0), 0) / answerTimings.length;
  }, [answerTimings]);

  const scoreMeaning = useMemo(() => {
    return getScoreMeaning(scoreSummary?.average_score || lastAnswerScore || 0, language);
  }, [scoreSummary, lastAnswerScore, language]);

  const topStrengthAreas = useMemo(() => {
    return getTopCategories(scoreSummary?.breakdown || [], language, 2);
  }, [scoreSummary, language]);

  const focusAreas = useMemo(() => {
    return getBottomCategories(scoreSummary?.breakdown || [], language, 2);
  }, [scoreSummary, language]);

  const handleSubmitAnswer = async (event) => {
    event.preventDefault();

    if (!answer.trim()) return;

    setSubmittingAnswer(true);
    setActionError("");

    const responseSeconds = Math.floor((Date.now() - questionStartedAt) / 1000);

    try {
      const cleanAnswer = answer.trim();

      const data = await interviewService.answerInterview(token, {
        session_id: Number(sessionId),
        answer: cleanAnswer,
      });

      setLastAnswerScore(data.score);
      setLastAnswerReview(data.review || null);

      const nextTimingRow = {
        questionIndex: transcript.filter((item) => item.role === "candidate").length + 1,
        seconds: responseSeconds,
        answeredAt: new Date().toISOString(),
      };

      persistTimings([...answerTimings, nextTimingRow]);
      setAnswer("");
      localStorage.removeItem(`${ANSWER_DRAFT_KEY_PREFIX}${sessionId}`);
      setQuestionStartedAt(Date.now());
      await loadData();
    } catch (error) {
      setActionError(getErrorMessage(error, "Failed to submit answer."));
    } finally {
      setSubmittingAnswer(false);
    }
  };

  const handleFinishInterview = async () => {
    setFinishingInterview(true);
    setActionError("");

    try {
      await interviewService.finishInterview(token, sessionId);
      await loadData();
    } catch (error) {
      setActionError(getErrorMessage(error, "Failed to finish interview."));
    } finally {
      setFinishingInterview(false);
    }
  };

  return {
    t,
    sessionId,
    language,
    session,
    transcript,
    scoreSummary,
    answerReviews,
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
  };
}