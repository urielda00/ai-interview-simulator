import ast
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path

from app.core.config import settings


logger = logging.getLogger(__name__)


HINT_KEYWORDS: dict[str, list[str]] = {
    "auth": [
        "auth",
        "authenticate",
        "authorization",
        "login",
        "logout",
        "token",
        "jwt",
        "password",
        "hash",
        "bcrypt",
        "session",
        "permission",
        "rbac",
        "oauth",
    ],
    "db": [
        "database",
        "db",
        "sql",
        "query",
        "sessionlocal",
        "sqlalchemy",
        "repository",
        "model",
        "migration",
        "engine",
        "orm",
        "postgres",
        "mysql",
        "sqlite",
        "mongo",
    ],
    "api": [
        "api",
        "router",
        "endpoint",
        "request",
        "response",
        "http",
        "fastapi",
        "flask",
        "express",
        "route",
        "controller",
        "schema",
    ],
    "validation": [
        "validate",
        "validation",
        "validator",
        "pydantic",
        "sanitize",
        "constraint",
        "check",
        "assert",
        "invalid",
    ],
    "logging": [
        "logger",
        "logging",
        "log",
        "traceback",
        "warning",
        "error",
        "info",
        "debug",
    ],
}


IMPORT_RE = re.compile(r"^\s*(?:from\s+([A-Za-z0-9_\.]+)\s+import|import\s+([A-Za-z0-9_\.]+))", re.MULTILINE)
FUNCTION_RE = re.compile(r"^\s*def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(", re.MULTILINE)
ASYNC_FUNCTION_RE = re.compile(r"^\s*async\s+def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(", re.MULTILINE)
CLASS_RE = re.compile(r"^\s*class\s+([A-Za-z_][A-Za-z0-9_]*)\s*(?:\(|:)", re.MULTILINE)


@dataclass
class CodeAnalysisResult:
    original_name: str
    stored_path: str
    readable: bool
    reason: str | None = None
    language: str | None = None
    size_bytes: int | None = None
    imports: list[str] = field(default_factory=list)
    functions: list[str] = field(default_factory=list)
    classes: list[str] = field(default_factory=list)
    async_functions: list[str] = field(default_factory=list)
    hints: list[str] = field(default_factory=list)
    content_excerpt: str = ""

    def has_real_signal(self) -> bool:
        return bool(
            self.readable
            and (
                self.imports
                or self.functions
                or self.classes
                or self.async_functions
                or self.hints
            )
        )


def _unique_keep_order(items: list[str], limit: int | None = None) -> list[str]:
    seen = set()
    result = []
    for item in items:
        cleaned = str(item).strip()
        if not cleaned or cleaned in seen:
            continue
        seen.add(cleaned)
        result.append(cleaned)
        if limit is not None and len(result) >= limit:
            break
    return result


def _detect_language(path: Path) -> str | None:
    ext = path.suffix.lower()
    mapping = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".jsx": "javascript",
        ".tsx": "typescript",
        ".java": "java",
        ".kt": "kotlin",
        ".go": "go",
        ".rb": "ruby",
        ".php": "php",
        ".cs": "csharp",
        ".cpp": "cpp",
        ".c": "c",
        ".h": "c",
        ".hpp": "cpp",
        ".swift": "swift",
        ".rs": "rust",
        ".scala": "scala",
        ".sql": "sql",
        ".json": "json",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".toml": "toml",
        ".ini": "ini",
        ".env": "env",
        ".md": "markdown",
        ".txt": "text",
        ".xml": "xml",
        ".html": "html",
        ".css": "css",
    }
    return mapping.get(ext)


def _is_probably_text_file(original_name: str, file_type: str | None) -> bool:
    ext = Path(original_name).suffix.lower()
    if ext in settings.PROJECT_AWARE_TEXT_EXTENSIONS:
        return True

    if not file_type:
        return False

    file_type_lower = file_type.lower()
    return any(file_type_lower.startswith(prefix) for prefix in settings.PROJECT_AWARE_TEXT_MIME_PREFIXES)


def _read_text_file(path: Path, max_bytes: int) -> tuple[bool, str | None, str, int]:
    if not path.exists() or not path.is_file():
        return False, "missing", "", 0

    size_bytes = path.stat().st_size
    if size_bytes > max_bytes:
        return False, "too_large", "", size_bytes

    raw = path.read_bytes()
    if b"\x00" in raw:
        return False, "binary", "", size_bytes

    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        try:
            text = raw.decode("utf-8", errors="ignore")
        except Exception:
            return False, "decode_failed", "", size_bytes

    return True, None, text, size_bytes


def _extract_hints(text: str, path_name: str) -> list[str]:
    haystack = f"{path_name}\n{text}".lower()
    hints = []

    for hint_name, keywords in HINT_KEYWORDS.items():
        if any(keyword in haystack for keyword in keywords):
            hints.append(hint_name)

    return hints


def _analyze_python_with_ast(text: str) -> tuple[list[str], list[str], list[str], list[str]]:
    tree = ast.parse(text)

    imports: list[str] = []
    functions: list[str] = []
    classes: list[str] = []
    async_functions: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            module_name = node.module or ""
            imports.append(module_name)
        elif isinstance(node, ast.FunctionDef):
            functions.append(node.name)
        elif isinstance(node, ast.AsyncFunctionDef):
            async_functions.append(node.name)
        elif isinstance(node, ast.ClassDef):
            classes.append(node.name)

    return (
        _unique_keep_order(imports, limit=12),
        _unique_keep_order(functions, limit=12),
        _unique_keep_order(classes, limit=12),
        _unique_keep_order(async_functions, limit=12),
    )


def _analyze_text_fallback(text: str) -> tuple[list[str], list[str], list[str], list[str]]:
    imports = []
    for left, right in IMPORT_RE.findall(text):
        imports.append(left or right)

    functions = FUNCTION_RE.findall(text)
    classes = CLASS_RE.findall(text)
    async_functions = ASYNC_FUNCTION_RE.findall(text)

    js_named_functions = re.findall(r"\bfunction\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(", text)
    js_const_functions = re.findall(
        r"\b(?:const|let|var)\s+([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(?:async\s*)?(?:\([^)]*\)|[A-Za-z_][A-Za-z0-9_]*)\s*=>",
        text,
    )
    if js_named_functions or js_const_functions:
        functions.extend(js_named_functions)
        functions.extend(js_const_functions)

    return (
        _unique_keep_order(imports, limit=12),
        _unique_keep_order(functions, limit=12),
        _unique_keep_order(classes, limit=12),
        _unique_keep_order(async_functions, limit=12),
    )


def analyze_uploaded_file(
    original_name: str,
    stored_path: str,
    file_type: str | None = None,
) -> CodeAnalysisResult:
    path = Path(stored_path)
    language = _detect_language(path)

    if not _is_probably_text_file(original_name=original_name, file_type=file_type):
        return CodeAnalysisResult(
            original_name=original_name,
            stored_path=stored_path,
            readable=False,
            reason="non_text_file",
            language=language,
        )

    is_readable, reason, text, size_bytes = _read_text_file(
        path=path,
        max_bytes=settings.PROJECT_AWARE_MAX_FILE_BYTES,
    )

    if not is_readable:
        return CodeAnalysisResult(
            original_name=original_name,
            stored_path=stored_path,
            readable=False,
            reason=reason,
            language=language,
            size_bytes=size_bytes,
        )

    text = text[: settings.PROJECT_AWARE_MAX_TOTAL_CHARS]

    imports: list[str] = []
    functions: list[str] = []
    classes: list[str] = []
    async_functions: list[str] = []

    if language == "python":
        try:
            imports, functions, classes, async_functions = _analyze_python_with_ast(text)
        except SyntaxError:
            logger.info("Python AST parsing failed for %s. Falling back to text parsing.", stored_path)
            imports, functions, classes, async_functions = _analyze_text_fallback(text)
        except Exception:
            logger.exception("Unexpected python AST parsing failure for %s", stored_path)
            imports, functions, classes, async_functions = _analyze_text_fallback(text)
    else:
        imports, functions, classes, async_functions = _analyze_text_fallback(text)

    hints = _unique_keep_order(_extract_hints(text=text, path_name=original_name), limit=8)

    excerpt_lines = [line.rstrip() for line in text.splitlines() if line.strip()][:8]
    content_excerpt = "\n".join(excerpt_lines)[:600]

    return CodeAnalysisResult(
        original_name=original_name,
        stored_path=stored_path,
        readable=True,
        reason=None,
        language=language,
        size_bytes=size_bytes,
        imports=imports,
        functions=functions,
        classes=classes,
        async_functions=async_functions,
        hints=hints,
        content_excerpt=content_excerpt,
    )


def analyze_uploaded_files(uploaded_files: list) -> list[CodeAnalysisResult]:
    results: list[CodeAnalysisResult] = []

    for uploaded_file in uploaded_files[: settings.PROJECT_AWARE_MAX_FILES]:
        results.append(
            analyze_uploaded_file(
                original_name=uploaded_file.original_name,
                stored_path=uploaded_file.stored_path,
                file_type=getattr(uploaded_file, "file_type", None),
            )
        )

    return results


def _format_list(items: list[str], limit: int = 3) -> str:
    selected = items[:limit]
    if not selected:
        return ""
    return ", ".join(selected)


def _build_questions_for_analysis(result: CodeAnalysisResult) -> list[str]:
    file_name = Path(result.original_name).name

    if not result.readable:
        if result.reason == "too_large":
            return [
                f"I could not read '{file_name}' because it is too large. How is this file structured, and why did it grow into a large unit instead of being split earlier?"
            ]
        if result.reason in {"binary", "non_text_file"}:
            return [
                f"'{file_name}' was not readable as a text source file. What role does it play in the project, and what architectural decisions does it connect to?"
            ]
        return [
            f"I could not read '{file_name}'. What responsibilities does this file own, and why did you place that logic there?"
        ]

    questions: list[str] = []

    if result.functions:
        questions.append(
            f"In '{file_name}', why did you center this flow around the function '{result.functions[0]}' instead of splitting that responsibility sooner?"
        )

    if result.async_functions:
        questions.append(
            f"In '{file_name}', what made '{result.async_functions[0]}' asynchronous, and what tradeoffs did that introduce around control flow or reliability?"
        )

    if result.classes:
        questions.append(
            f"In '{file_name}', why does the class '{result.classes[0]}' exist as a separate abstraction, and how would you refactor it if the system grows?"
        )

    if result.imports:
        questions.append(
            f"In '{file_name}', this file depends on imports like { _format_list(result.imports) }. Why do those dependencies belong here, and what coupling risks do they create?"
        )

    if "auth" in result.hints:
        questions.append(
            f"'{file_name}' looks tied to authentication or authorization. Why did you centralize auth-related logic here, and what tradeoff does that create for maintainability?"
        )

    if "db" in result.hints:
        questions.append(
            f"'{file_name}' seems to touch database concerns. How did you decide what data-access responsibility belongs here versus in a repository or service layer?"
        )

    if "api" in result.hints:
        questions.append(
            f"'{file_name}' looks close to the API layer. How did you decide what should stay in the endpoint contract versus move into deeper business logic?"
        )

    if "validation" in result.hints:
        questions.append(
            f"In '{file_name}', I can see validation-related concerns. Why did you place validation at this layer, and how do you avoid duplicating those checks elsewhere?"
        )

    if "logging" in result.hints:
        questions.append(
            f"'{file_name}' includes logging-related behavior. How did you decide what is important enough to log here without creating noisy or low-signal observability?"
        )

    if not questions:
        questions.append(
            f"I read '{file_name}'. What responsibilities does this file own, and what would be the first thing you would refactor if the project became much larger?"
        )

    return _unique_keep_order(questions, limit=6)


def build_project_aware_questions(uploaded_files: list) -> list[str]:
    analyses = analyze_uploaded_files(uploaded_files)

    questions: list[str] = []
    for result in analyses:
        questions.extend(_build_questions_for_analysis(result))

    questions = _unique_keep_order(questions, limit=settings.PROJECT_AWARE_MAX_FILES)

    if questions:
        return questions

    return [
        "You selected project-aware mode, but I could not extract enough signal from the uploaded files. Describe the architecture of your project and the main design decisions behind it.",
        "What tradeoffs did you make in the project structure?",
        "What would you refactor first if the system had to scale?",
    ]