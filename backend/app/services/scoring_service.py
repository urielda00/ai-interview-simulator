from app.services.ai_service import score_answer_with_openai


def _clamp_score(value: float) -> float:
    return round(max(0.0, min(value, 10.0)), 2)


def _extract_standard_strengths_and_weaknesses(answer: str) -> tuple[str, str]:
    text = answer.strip()
    text_lower = text.lower()
    word_count = len(text.split())

    strengths = []
    weaknesses = []

    if word_count >= 20:
        strengths.append("Answer had enough detail to show a fuller thought process.")
    else:
        weaknesses.append("Answer was too short and likely felt shallow in an interview.")

    if any(term in text_lower for term in ["because", "for example", "example"]):
        strengths.append("Included some explanation or supporting example.")
    else:
        weaknesses.append("Could use clearer reasoning or an example to support the point.")

    if any(
        term in text_lower
        for term in [
            "authentication",
            "authorization",
            "jwt",
            "token",
            "middleware",
            "database",
            "validation",
            "hash",
            "encryption",
            "security",
            "session",
            "rbac",
        ]
    ):
        strengths.append("Referenced relevant technical concepts.")
    else:
        weaknesses.append("Missing concrete technical terminology.")

    if any(term in text_lower for term in ["tradeoff", "pros", "cons"]):
        strengths.append("Showed some awareness of tradeoffs.")
    else:
        weaknesses.append("Did not discuss tradeoffs or alternatives.")

    return " ".join(strengths), " ".join(weaknesses)


def _extract_leetcode_strengths_and_weaknesses(answer: str) -> tuple[str, str]:
    text = answer.strip()
    text_lower = text.lower()
    word_count = len(text.split())

    strengths = []
    weaknesses = []

    if any(term in text_lower for term in ["o(", "time complexity", "space complexity"]):
        strengths.append("Covered algorithmic complexity.")
    else:
        weaknesses.append("Did not explain time or space complexity.")

    if any(
        term in text_lower
        for term in ["hash map", "hashmap", "dict", "dictionary", "stack", "queue", "pointer", "set", "array"]
    ):
        strengths.append("Referenced concrete data structures.")
    else:
        weaknesses.append("Could be stronger by naming the data structure choice explicitly.")

    if "edge case" in text_lower:
        strengths.append("Mentioned edge cases.")
    else:
        weaknesses.append("Did not address edge cases.")

    if word_count < 15:
        weaknesses.append("Explanation was brief and may not sound strong in a live interview.")

    return " ".join(strengths), " ".join(weaknesses)


def _extract_project_strengths_and_weaknesses(answer: str) -> tuple[str, str]:
    text = answer.strip()
    text_lower = text.lower()
    word_count = len(text.split())

    strengths = []
    weaknesses = []

    if any(term in text_lower for term in ["architecture", "responsibilities", "layer", "separate", "isolated"]):
        strengths.append("Showed architectural thinking.")
    else:
        weaknesses.append("Could explain architecture and responsibility boundaries more clearly.")

    if any(term in text_lower for term in ["maintain", "maintainability", "testing", "scaling"]):
        strengths.append("Touched on maintainability or long-term quality.")
    else:
        weaknesses.append("Did not show enough maintainability or scaling thinking.")

    if any(term in text_lower for term in ["tradeoff", "abstraction"]):
        strengths.append("Referenced design tradeoffs.")
    else:
        weaknesses.append("Could be stronger by explaining why this design was chosen over alternatives.")

    if word_count < 20:
        weaknesses.append("Project explanation was likely too brief for a strong project-defense answer.")

    return " ".join(strengths), " ".join(weaknesses)


def _fallback_standard_breakdown(answer: str) -> dict:
    text = answer.strip()
    text_lower = text.lower()
    word_count = len(text.split())

    clarity = 3.0
    technical_accuracy = 2.5
    depth = 2.0
    tradeoff_reasoning = 1.5
    confidence = 0.78

    if word_count >= 10:
        clarity += 1.0
    if word_count >= 20:
        clarity += 1.0
        depth += 1.0
    if word_count >= 35:
        depth += 1.0

    technical_keywords = [
        "security",
        "database",
        "token",
        "session",
        "authorization",
        "authentication",
        "middleware",
        "validation",
        "hash",
        "encryption",
        "jwt",
        "rbac",
    ]
    keyword_hits = sum(1 for keyword in technical_keywords if keyword in text_lower)
    technical_accuracy += min(keyword_hits * 0.4, 3.0)

    if "because" in text_lower or "for example" in text_lower or "example" in text_lower:
        clarity += 0.7

    if "tradeoff" in text_lower or "pros" in text_lower or "cons" in text_lower:
        tradeoff_reasoning += 2.0

    if "scalability" in text_lower or "performance" in text_lower or "edge case" in text_lower:
        depth += 1.0

    breakdown = [
        {"category": "clarity", "score": _clamp_score(clarity), "confidence": confidence},
        {"category": "technical_accuracy", "score": _clamp_score(technical_accuracy), "confidence": confidence},
        {"category": "depth", "score": _clamp_score(depth), "confidence": confidence},
        {"category": "tradeoff_reasoning", "score": _clamp_score(tradeoff_reasoning), "confidence": confidence},
    ]

    avg_score = round(sum(item["score"] for item in breakdown) / len(breakdown), 2)
    strengths, weaknesses = _extract_standard_strengths_and_weaknesses(answer)

    return {
        "score": avg_score,
        "confidence": confidence,
        "reason": "Fallback local heuristic scoring was used.",
        "strengths": strengths,
        "weaknesses": weaknesses,
        "source": "fallback",
        "fallback_reason": "ai_unavailable_or_failed",
        "breakdown": breakdown,
    }


def _fallback_leetcode_breakdown(answer: str) -> dict:
    text = answer.strip().lower()
    word_count = len(answer.split())

    correctness = 2.5
    complexity_analysis = 2.0
    data_structures = 2.0
    communication = 2.0
    confidence = 0.78

    if word_count >= 15:
        communication += 1.0
    if word_count >= 30:
        communication += 1.0

    if "o(" in text or "time complexity" in text:
        complexity_analysis += 3.0

    if "space complexity" in text:
        complexity_analysis += 1.5

    structures = ["hash map", "hashmap", "dict", "dictionary", "stack", "queue", "pointer", "set", "array"]
    if any(item in text for item in structures):
        data_structures += 2.5
        correctness += 1.0

    if "edge case" in text:
        correctness += 1.0

    code_markers = ["def ", "return ", "for ", "while ", "if ", "class "]
    if any(marker in answer for marker in code_markers):
        correctness += 1.2

    breakdown = [
        {"category": "correctness", "score": _clamp_score(correctness), "confidence": confidence},
        {"category": "complexity_analysis", "score": _clamp_score(complexity_analysis), "confidence": confidence},
        {"category": "data_structures", "score": _clamp_score(data_structures), "confidence": confidence},
        {"category": "communication", "score": _clamp_score(communication), "confidence": confidence},
    ]

    avg_score = round(sum(item["score"] for item in breakdown) / len(breakdown), 2)
    strengths, weaknesses = _extract_leetcode_strengths_and_weaknesses(answer)

    return {
        "score": avg_score,
        "confidence": confidence,
        "reason": "Fallback local heuristic scoring was used.",
        "strengths": strengths,
        "weaknesses": weaknesses,
        "source": "fallback",
        "fallback_reason": "ai_unavailable_or_failed",
        "breakdown": breakdown,
    }


def _fallback_project_breakdown(answer: str) -> dict:
    text = answer.strip().lower()
    word_count = len(answer.split())

    architecture_reasoning = 2.5
    maintainability = 2.5
    tradeoff_reasoning = 2.0
    communication = 2.0
    confidence = 0.78

    if word_count >= 15:
        communication += 1.0
    if word_count >= 30:
        communication += 1.0

    if "maintain" in text or "maintainability" in text or "testing" in text or "scaling" in text:
        maintainability += 2.0

    if "tradeoff" in text or "abstraction" in text or "layer" in text:
        tradeoff_reasoning += 2.0

    if "architecture" in text or "responsibilities" in text or "separate" in text or "isolated" in text:
        architecture_reasoning += 2.0

    breakdown = [
        {"category": "architecture_reasoning", "score": _clamp_score(architecture_reasoning), "confidence": confidence},
        {"category": "maintainability", "score": _clamp_score(maintainability), "confidence": confidence},
        {"category": "tradeoff_reasoning", "score": _clamp_score(tradeoff_reasoning), "confidence": confidence},
        {"category": "communication", "score": _clamp_score(communication), "confidence": confidence},
    ]

    avg_score = round(sum(item["score"] for item in breakdown) / len(breakdown), 2)
    strengths, weaknesses = _extract_project_strengths_and_weaknesses(answer)

    return {
        "score": avg_score,
        "confidence": confidence,
        "reason": "Fallback local heuristic scoring was used.",
        "strengths": strengths,
        "weaknesses": weaknesses,
        "source": "fallback",
        "fallback_reason": "ai_unavailable_or_failed",
        "breakdown": breakdown,
    }


def score_answer(
    question: str,
    answer: str,
    track: str,
    level: str,
    mode: str,
    language: str,
) -> dict:
    ai_score = score_answer_with_openai(
        question=question,
        answer=answer,
        track=track,
        level=level,
        mode=mode,
        language=language,
    )

    if ai_score:
        breakdown = ai_score.get("breakdown", [])
        if breakdown:
            avg_score = round(sum(item["score"] for item in breakdown) / len(breakdown), 2)
        else:
            avg_score = ai_score["score"]

        return {
            "score": avg_score,
            "confidence": ai_score["confidence"],
            "reason": ai_score.get("reason", ""),
            "strengths": ai_score.get("strengths", ""),
            "weaknesses": ai_score.get("weaknesses", ""),
            "source": "ai",
            "fallback_reason": None,
            "breakdown": breakdown,
        }

    mode_lower = mode.lower()
    if mode_lower == "leetcode":
        return _fallback_leetcode_breakdown(answer)
    if mode_lower == "project_aware":
        return _fallback_project_breakdown(answer)
    return _fallback_standard_breakdown(answer)