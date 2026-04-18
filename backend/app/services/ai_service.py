import json
import logging
from typing import Any

from app.core.config import settings
from app.core.i18n import llm_language_instruction, llm_language_name

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


logger = logging.getLogger(__name__)


def has_openai() -> bool:
    return bool(settings.OPENAI_API_KEY and settings.OPENAI_MODEL and OpenAI is not None)


def get_ai_provider_status() -> dict[str, Any]:
    return {
        "enabled": has_openai(),
        "provider": "openai",
        "model": settings.OPENAI_MODEL or None,
        "timeout_seconds": settings.OPENAI_TIMEOUT_SECONDS,
        "max_retries": settings.OPENAI_MAX_RETRIES,
    }


def _get_client():
    if not has_openai():
        return None

    return OpenAI(
        api_key=settings.OPENAI_API_KEY,
        timeout=settings.OPENAI_TIMEOUT_SECONDS,
        max_retries=settings.OPENAI_MAX_RETRIES,
    )


def _safe_parse_json(text: str) -> dict[str, Any] | None:
    text = text.strip()

    try:
        return json.loads(text)
    except Exception:
        pass

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start:end + 1])
        except Exception:
            return None

    return None


def _classify_exception(exc: Exception) -> str:
    text = str(exc).lower()

    if "timeout" in text:
        return "timeout"
    if "rate limit" in text:
        return "rate_limit"
    if "authentication" in text or "api key" in text:
        return "auth_error"
    if "connection" in text or "network" in text:
        return "network_error"
    return "provider_error"


def _normalize_score_to_0_10(score: float) -> float:
    normalized = float(score)

    if 0.0 <= normalized <= 1.0:
        logger.warning("OpenAI returned score on 0-1 scale. Auto-normalizing to 0-10. raw_score=%s", normalized)
        normalized *= 10.0

    return max(0.0, min(normalized, 10.0))


def _normalize_breakdown(
    parsed_breakdown: Any,
    rubric: list[str],
    default_confidence: float,
) -> list[dict[str, Any]] | None:
    if not isinstance(parsed_breakdown, list):
        return None

    breakdown_map: dict[str, dict[str, Any]] = {}

    for item in parsed_breakdown:
        if not isinstance(item, dict):
            continue

        category = str(item.get("category", "")).strip()
        if not category or category not in rubric:
            continue

        try:
            score = float(item.get("score", 0))
        except Exception:
            continue

        confidence_raw = item.get("confidence", default_confidence)
        try:
            confidence = float(confidence_raw) if confidence_raw is not None else default_confidence
        except Exception:
            confidence = default_confidence

        normalized_score = _normalize_score_to_0_10(score)

        breakdown_map[category] = {
            "category": category,
            "score": normalized_score,
            "confidence": max(0.0, min(confidence, 1.0)),
        }

    if not breakdown_map:
        return None

    normalized = []
    for category in rubric:
        if category in breakdown_map:
            normalized.append(breakdown_map[category])

    return normalized if normalized else None


def _chat_completion(messages: list[dict[str, str]], temperature: float) -> str | None:
    client = _get_client()
    if not client:
        logger.info("OpenAI provider unavailable. Falling back to local behavior.")
        return None

    try:
        logger.info(
            "Calling OpenAI. model=%s temperature=%s message_count=%s",
            settings.OPENAI_MODEL,
            temperature,
            len(messages),
        )

        response = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            temperature=temperature,
            messages=messages,
        )

        content = response.choices[0].message.content
        if not content:
            logger.warning("OpenAI returned empty content.")
            return None

        logger.info("OpenAI call succeeded.")
        return content.strip()

    except Exception as exc:
        error_type = _classify_exception(exc)
        logger.warning("OpenAI chat completion failed. type=%s error=%s", error_type, str(exc))
        return None


def _get_rubric_for_mode(mode: str) -> list[str]:
    mode_lower = mode.lower()

    if mode_lower == "leetcode":
        return [
            "correctness",
            "complexity_analysis",
            "data_structures",
            "communication",
        ]

    if mode_lower == "project_aware":
        return [
            "architecture_reasoning",
            "maintainability",
            "tradeoff_reasoning",
            "communication",
        ]

    return [
        "clarity",
        "technical_accuracy",
        "depth",
        "tradeoff_reasoning",
    ]


def generate_followup_with_openai(
    question: str,
    answer: str,
    track: str,
    level: str,
    mode: str,
    language: str,
) -> str | None:
    prompt = f"""
You are a sharp technical interviewer.

Track: {track}
Level: {level}
Mode: {mode}
Output language: {llm_language_name(language)}

Language instruction:
{llm_language_instruction(language)}

Current question:
{question}

Candidate answer:
{answer}

Return exactly one concise technical follow-up question.
Do not include explanations, numbering, or extra text.
""".strip()

    return _chat_completion(
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a strict but helpful technical interviewer. "
                    f"{llm_language_instruction(language)}"
                ),
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
    )


def score_answer_with_openai(
    question: str,
    answer: str,
    track: str,
    level: str,
    mode: str,
    language: str,
) -> dict[str, Any] | None:
    rubric = _get_rubric_for_mode(mode)

    prompt = f"""
You are grading a mock interview answer.

Track: {track}
Level: {level}
Mode: {mode}
Output language: {llm_language_name(language)}

Language instruction:
{llm_language_instruction(language)}

Question:
{question}

Candidate answer:
{answer}

Use this scoring rubric exactly:
{json.dumps(rubric)}

Important scoring rule:
- Every score in this response must use a 0 to 10 scale
- Do not use 0 to 1 for score
- confidence alone should use a 0 to 1 scale

Return JSON only with this exact shape:
{{
  "score": 0-10 number,
  "confidence": 0-1 number,
  "reason": "short explanation",
  "strengths": "short strengths",
  "weaknesses": "short weaknesses",
  "breakdown": [
    {{
      "category": "{rubric[0]}",
      "score": 0-10 number,
      "confidence": 0-1 number
    }}
  ]
}}

Rules:
- breakdown must contain one item for each rubric category
- category names must match the rubric exactly
- overall score should align with the average quality of the breakdown
- return JSON only
""".strip()

    content = _chat_completion(
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a strict technical evaluator. Return JSON only. "
                    f"{llm_language_instruction(language)}"
                ),
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
    )
    if not content:
        return None

    parsed = _safe_parse_json(content)
    if not parsed:
        logger.warning("OpenAI scoring response could not be parsed as JSON.")
        return None

    try:
        score = float(parsed.get("score", 0))
        confidence = float(parsed.get("confidence", 0.75))
    except Exception:
        logger.warning("OpenAI scoring response contained invalid numeric fields.")
        return None

    confidence = max(0.0, min(confidence, 1.0))
    normalized_score = _normalize_score_to_0_10(score)

    breakdown = _normalize_breakdown(parsed.get("breakdown"), rubric, confidence)
    if not breakdown:
        logger.warning("OpenAI scoring response did not include a valid rubric breakdown.")
        return None

    return {
        "score": normalized_score,
        "confidence": confidence,
        "reason": str(parsed.get("reason", "")).strip(),
        "strengths": str(parsed.get("strengths", "")).strip(),
        "weaknesses": str(parsed.get("weaknesses", "")).strip(),
        "breakdown": breakdown,
    }


def build_report_with_openai(
    transcript: list[dict[str, Any]],
    scores: list[dict[str, Any]],
    track: str,
    level: str,
    mode: str,
    language: str,
) -> dict[str, str] | None:
    prompt = f"""
You are generating a final interview report.

Track: {track}
Level: {level}
Mode: {mode}
Output language: {llm_language_name(language)}

Language instruction:
{llm_language_instruction(language)}

Transcript:
{json.dumps(transcript, ensure_ascii=False)}

Scores:
{json.dumps(scores, ensure_ascii=False)}

Return JSON only with this exact shape:
{{
  "summary": "2-3 sentences",
  "strengths": "short paragraph",
  "weaknesses": "short paragraph",
  "study_plan": "short paragraph"
}}
""".strip()

    content = _chat_completion(
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a technical interview report writer. Return JSON only. "
                    f"{llm_language_instruction(language)}"
                ),
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
    )
    if not content:
        return None

    parsed = _safe_parse_json(content)
    if not parsed:
        logger.warning("OpenAI report response could not be parsed as JSON.")
        return None

    return {
        "summary": str(parsed.get("summary", "")).strip(),
        "strengths": str(parsed.get("strengths", "")).strip(),
        "weaknesses": str(parsed.get("weaknesses", "")).strip(),
        "study_plan": str(parsed.get("study_plan", "")).strip(),
    }