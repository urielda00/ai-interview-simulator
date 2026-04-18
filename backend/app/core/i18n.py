from typing import Optional


SUPPORTED_LANGUAGES = {"en", "he"}


def normalize_language(language: Optional[str] = None, accept_language: Optional[str] = None) -> str:
    if language:
        lang = language.strip().lower()
        if lang.startswith("he"):
            return "he"
        if lang.startswith("en"):
            return "en"

    if accept_language:
        value = accept_language.strip().lower()
        if value.startswith("he"):
            return "he"
        if value.startswith("en"):
            return "en"

    return "en"


def llm_language_name(language: str) -> str:
    return "Hebrew" if language == "he" else "English"


def llm_language_instruction(language: str) -> str:
    if language == "he":
        return (
            "Respond in natural Hebrew. "
            "Keep common technical terms in English when appropriate, such as JWT, middleware, hash map, "
            "REST API, token, backend, database, caching, validation, authorization, authentication. "
            "Do not force awkward Hebrew translations for such terms."
        )

    return "Respond in natural English."


def is_hebrew_text(text: str) -> bool:
    return any("\u0590" <= ch <= "\u05FF" for ch in text)