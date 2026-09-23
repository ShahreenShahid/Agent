"""Generate the Space Fractions project from architecture documentation.

Install the SDK with: pip install google-genai
Set GEMINI_API_KEY before running this script.
"""

from __future__ import annotations

import os
import argparse
import json
import re
import sys
import time
from pathlib import Path
from typing import Any

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

if load_dotenv is not None:
    load_dotenv()

try:
    from google import genai
    from google.genai import types
except ImportError:  # The CLI can still expose --help before setup is complete.
    genai = None  # type: ignore[assignment]
    types = None  # type: ignore[assignment]


PROJECT_NAME = "space-fractions"
DEFAULT_DOCUMENTATION = "Architecture_Documentation.md"
DEFAULT_VIEW = "Architecture_View.md"
DEFAULT_OUTPUT = "output"
MAX_RETRIES = 3

REQUIRED_FILES: dict[str, str] = {
    "package.json": "Node.js package metadata, scripts, and runtime dependencies.",
    "src/app.js": "Express application entry point with health and game API routes.",
    "src/components/game.js": "Game component containing game state and scoring logic.",
    "src/components/question.js": "Question component for retrieving and checking questions.",
    "src/components/user.js": "User component for identity, authorization, and score access.",
    "sql/game_ddl.sql": "PostgreSQL DDL for games and durable game state.",
    "sql/question_ddl.sql": "PostgreSQL DDL for questions and answer data.",
    "proto/internal.proto": "Internal GameService protobuf contract.",
    "openapi.yaml": "OpenAPI contract for the public Space Fractions API.",
    "k8s/spacefractions-deployment.yaml": "Kubernetes deployment manifest for the service.",
    "test/app.test.js": "Unit and API tests for the generated application.",
    "README.md": "Setup, architecture, API, testing, and deployment documentation.",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a Space Fractions project from architecture markdown files."
    )
    parser.add_argument("--documentation", default=DEFAULT_DOCUMENTATION)
    parser.add_argument("--view", default=DEFAULT_VIEW)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    return parser.parse_args()


def read_required_file(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise SystemExit(f"Input file not found: {path}") from exc
    except OSError as exc:
        raise SystemExit(f"Could not read input file {path}: {exc}") from exc


def strip_code_fences(value: str) -> str:
    """Remove accidental Markdown fences without changing the generated source."""
    cleaned = value.strip()
    cleaned = re.sub(r"^```[\w.+-]*\s*\n", "", cleaned, count=1)
    cleaned = re.sub(r"\n```\s*$", "", cleaned, count=1)
    return cleaned.strip()


def parse_json_response(text: str) -> dict[str, Any]:
    cleaned = strip_code_fences(text)
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
        if not match:
            raise ValueError("Gemini returned invalid JSON with no JSON object.")
        parsed = json.loads(match.group(0))
    if not isinstance(parsed, dict):
        raise ValueError("Gemini plan must be a JSON object.")
    return parsed


def is_authentication_error(error: Exception) -> bool:
    message = str(error).lower()
    return "api_key_invalid" in message or "api key not valid" in message


def is_transient_error(error: Exception) -> bool:
    message = str(error).lower()
    return any(
        marker in message
        for marker in ("503 unavailable", "service unavailable", "429", "resource exhausted")
    )


def is_model_unavailable_error(error: Exception) -> bool:
    return "404 not_found" in str(error).lower() or "no longer available" in str(error).lower()


def is_quota_error(error: Exception) -> bool:
    message = str(error).lower()
    return "quota exceeded" in message or "resource_exhausted" in message


def is_text_flash_model(name: str) -> bool:
    lowered = name.lower()
    excluded_markers = ("image", "tts", "audio", "embedding", "robotics", "computer-use")
    return "flash" in lowered and not any(marker in lowered for marker in excluded_markers)


def model_supports_generate_content(model: Any) -> bool:
    supported_actions = getattr(model, "supported_actions", None)
    if not supported_actions:
        return True
    return any(
        str(action).lower().replace("_", "") in {"generatecontent", "generatecontentaction"}
        for action in supported_actions
    )


def model_priority(name: str) -> tuple[int, str]:
    lowered = name.lower()
    if is_text_flash_model(name):
        return (0, lowered)
    if "pro" in lowered and not any(marker in lowered for marker in ("image", "tts", "audio")):
        return (1, lowered)
    return (2, lowered)


def resolve_models(client: Any) -> list[str]:
    """Discover text-capable generateContent models and order them by usefulness."""
    try:
        available: set[str] = set()
        for model in client.models.list():
            raw_name = str(getattr(model, "name", ""))
            name = raw_name.removeprefix("models/")
            if name and model_supports_generate_content(model) and is_text_model(name):
                available.add(name)
    except Exception as exc:
        if is_authentication_error(exc):
            raise RuntimeError(
                "Google rejected GEMINI_API_KEY. Create a valid Gemini API key and set it "
                "in the current terminal session before running agent.py."
            ) from exc
        raise RuntimeError(
            f"Could not discover Gemini models: {exc}. Check GEMINI_API_KEY and network access."
        ) from exc

    requested = os.environ.get("GEMINI_MODEL")
    candidates = sorted(available, key=model_priority)
    if requested:
        requested = requested.removeprefix("models/")
        if requested in available:
            candidates.remove(requested)
            candidates.insert(0, requested)
        else:
            print(f"Warning: GEMINI_MODEL={requested} is not an available text model; ignoring it.")
    if candidates:
        return candidates

    choices = ", ".join(sorted(available)) or "none"
    raise RuntimeError(
        f"No active text model supports generateContent. Available models: {choices}."
    )


def is_text_model(name: str) -> bool:
    lowered = name.lower()
    excluded_markers = (
        "image",
        "tts",
        "audio",
        "embedding",
        "robotics",
        "computer-use",
        "aqa",
        "transcribe",
        "lyria",
        "nano-banana",
        "antigravity",
        "deep-research",
        "gemma",
    )
    is_text_generation_family = "flash" in lowered or "pro" in lowered
    return is_text_generation_family and not any(
        marker in lowered for marker in excluded_markers
    )


def generate_content(
    client: Any,
    model_names: list[str],
    prompt: str,
    *,
    json_mode: bool = False,
) -> str:
    config = types.GenerateContentConfig(
        temperature=0.2,
        response_mime_type="application/json" if json_mode else "text/plain",
    )
    last_error: Exception | None = None
    for model_index, model_name in enumerate(model_names):
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                chat = client.chats.create(model=model_name, config=config)
                response = chat.send_message(message=prompt)
                text = response.text
                if not text:
                    raise ValueError("Gemini returned an empty response.")
                return text
            except Exception as exc:  # SDK errors vary by installed SDK version.
                if is_authentication_error(exc):
                    raise RuntimeError(
                        "Google rejected GEMINI_API_KEY. Create a valid Gemini API key and set it "
                        "in the current terminal session before running agent.py."
                    ) from exc
                last_error = exc
                if is_model_unavailable_error(exc):
                    print(f"    Skipping unavailable model: {model_name}")
                    break
                if is_quota_error(exc) and model_index + 1 < len(model_names):
                    print(
                        f"    {model_name} quota is exhausted; "
                        f"trying {model_names[model_index + 1]}."
                    )
                    break
                if is_transient_error(exc) and model_index + 1 < len(model_names):
                    print(
                        f"    {model_name} is temporarily unavailable; "
                        f"trying {model_names[model_index + 1]}."
                    )
                    break
                if is_quota_error(exc):
                    raise RuntimeError(
                        f"Gemini quota is exhausted for the available text models. Details: {exc}"
                    ) from exc
                if attempt == MAX_RETRIES:
                    break
                delay = 2**attempt
                print(f"    {model_name} attempt {attempt} failed; retrying in {delay}s: {exc}")
                time.sleep(delay)
    if last_error is not None and is_transient_error(last_error):
        raise RuntimeError(
            "All available text Gemini models are temporarily unavailable. "
            "Wait a few minutes and run agent.py again. "
            f"Last provider response: {last_error}"
        ) from last_error
    raise RuntimeError(f"Gemini request failed after {MAX_RETRIES} attempts: {last_error}")


def build_plan(
    client: Any,
    model_names: list[str],
    documentation: str,
    view: str,
) -> dict[str, Any]:
    prompt = f"""You are the lead engineer planning a production-ready educational game repository.
Convert the architecture documentation and all PlantUML diagrams below into a JSON execution plan.
Return JSON only, with exactly this top-level shape:
{{"project_name":"space-fractions","files":[{{"path":"relative/path","description":"what complete code belongs there"}}]}}

The files list must cover at least every required artifact below. Add other files only when they
are needed for a runnable Node.js 18+ Express project. Paths must be relative to the project root.
Required artifacts:
{json.dumps(REQUIRED_FILES, indent=2)}

Architecture documentation:
---
{documentation}
---
Architecture and UML views:
---
{view}
---
"""
    plan = parse_json_response(generate_content(client, model_names, prompt, json_mode=True))
    return normalize_plan(plan)


def normalize_plan(plan: dict[str, Any]) -> dict[str, Any]:
    if plan.get("project_name") != PROJECT_NAME:
        plan["project_name"] = PROJECT_NAME
    raw_files = plan.get("files")
    if not isinstance(raw_files, list):
        raw_files = []

    files: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in raw_files:
        if not isinstance(item, dict) or not isinstance(item.get("path"), str):
            continue
        path = item["path"].replace("\\", "/").lstrip("./")
        if not path or path in seen or Path(path).is_absolute() or ".." in Path(path).parts:
            continue
        seen.add(path)
        files.append({
            "path": path,
            "description": str(item.get("description", "Implement this repository artifact.")),
        })

    for path, description in REQUIRED_FILES.items():
        if path not in seen:
            files.append({"path": path, "description": description})
    return {"project_name": PROJECT_NAME, "files": files}


def targeted_context(documentation: str, view: str, path: str) -> str:
    name = path.lower()
    keyword_groups = {
        "app": ("api", "express", "component", "deployment", "security"),
        "game": ("game", "play", "score", "state", "sequence", "activity"),
        "question": ("question", "answer", "sql", "sequence", "class"),
        "user": ("user", "oauth", "auth", "score", "class"),
        "openapi": ("openapi", "external api", "/play", "rest"),
        "proto": ("proto", "internal", "gameservice", "rpc"),
        "sql": ("sql", "table", "schema", "question", "game"),
        "k8s": ("kubernetes", "deployment", "container", "replicas"),
        "test": ("testing", "qa", "requirement", "api"),
        "readme": ("overview", "deployment", "testing", "api", "setup"),
        "package": ("node.js", "express", "runtime", "technology"),
    }
    keywords: tuple[str, ...] = ()
    for marker, marker_keywords in keyword_groups.items():
        if marker in name:
            keywords += marker_keywords

    def select_blocks(source: str) -> list[str]:
        blocks = re.split(r"(?=^#{1,6}\s|^```plantuml\s*$)", source, flags=re.MULTILINE)
        selected = [
            block.strip()
            for block in blocks
            if any(keyword in block.lower() for keyword in keywords)
        ]
        return selected

    selected = select_blocks(documentation) + select_blocks(view)
    if not selected:
        selected = [documentation[:8000], view[:8000]]
    return "\n\n--- Relevant architecture context ---\n\n".join(selected)[:18000]


def safe_output_path(root: Path, relative_path: str) -> Path:
    normalized = relative_path.replace("\\", "/")
    candidate = (root / normalized).resolve()
    if candidate != root.resolve() and root.resolve() not in candidate.parents:
        raise ValueError(f"Refusing to write outside output directory: {relative_path}")
    return candidate


def generate_file(
    client: Any,
    model_names: list[str],
    project_root: Path,
    item: dict[str, str],
    documentation: str,
    view: str,
) -> None:
    path = item["path"]
    output_path = safe_output_path(project_root, path)
    context = targeted_context(documentation, view, path)
    prompt = f"""Generate the complete contents of the repository file `{path}` for the Space Fractions project.
Description: {item['description']}

Use the architecture context below as the source of truth. Produce working, production-quality code
that integrates with the other planned files. Respect the file format, Node.js 18+ compatibility,
Express conventions, API contracts, SQL/protobuf/YAML validity, security requirements, and tests.
Do not explain anything. Return only the raw file contents, with no Markdown fences or surrounding prose.

{context}
"""
    content = strip_code_fences(generate_content(client, model_names, prompt))
    if not content:
        raise ValueError(f"Gemini generated empty content for {path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    if genai is None or types is None:
        print(
            "Missing dependency: install the official SDK with 'pip install google-genai'.",
            file=sys.stderr,
        )
        return 2
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY is not set.", file=sys.stderr)
        return 2

    documentation = read_required_file(Path(args.documentation))
    view = read_required_file(Path(args.view))
    output_root = Path(args.output).resolve()
    project_root = output_root / PROJECT_NAME
    client = genai.Client(api_key=api_key)

    print("[1/3] Generating Plan...")
    try:
        model_names = resolve_models(client)
        print(f"    Using Gemini model: {model_names[0]}")
        if len(model_names) > 1:
            print(f"    Failover models: {', '.join(model_names[1:])}")
        plan = build_plan(client, model_names, documentation, view)
    except (RuntimeError, ValueError, TypeError, json.JSONDecodeError) as exc:
        print(f"Error while generating architecture plan: {exc}", file=sys.stderr)
        return 1

    output_root.mkdir(parents=True, exist_ok=True)
    plan_path = output_root / "architecture_plan.json"
    plan_path.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
    print(f"    Saved {plan_path}")

    print(f"[2/3] Generating {len(plan['files'])} project files...")
    for index, item in enumerate(plan["files"], start=1):
        print(f"[2/3] Writing file {index}/{len(plan['files'])}: {item['path']}...")
        try:
            generate_file(client, model_names, project_root, item, documentation, view)
        except (RuntimeError, ValueError, OSError) as exc:
            print(f"Error while generating {item['path']}: {exc}", file=sys.stderr)
            return 1

    print("[3/3] Generation complete.")
    print(f"    Project: {project_root}")
    print(f"    Plan: {plan_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())