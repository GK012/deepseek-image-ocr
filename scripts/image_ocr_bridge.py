#!/usr/bin/env python3
"""OCR image evidence and optionally ask a DeepSeek-compatible text model."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path


def image_metadata(path: Path) -> dict:
    metadata = {
        "path": str(path),
        "filename": path.name,
        "bytes": path.stat().st_size,
    }
    try:
        from PIL import Image

        with Image.open(path) as image:
            metadata.update(
                {
                    "width": image.width,
                    "height": image.height,
                    "mode": image.mode,
                    "format": image.format,
                }
            )
    except Exception as exc:  # Pillow is optional.
        metadata["image_probe_warning"] = str(exc)
    return metadata


def run_tesseract(path: Path, lang: str, psm: str | None) -> tuple[str, str | None]:
    executable = shutil.which("tesseract")
    if not executable:
        return "", "tesseract executable not found on PATH"

    command = [executable, str(path), "stdout", "-l", lang]
    if psm:
        command.extend(["--psm", psm])

    try:
        completed = subprocess.run(
            command,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding="utf-8",
            errors="replace",
        )
    except Exception as exc:
        return "", f"failed to run tesseract: {exc}"

    warning = completed.stderr.strip() or None
    if completed.returncode != 0:
        return completed.stdout.strip(), warning or f"tesseract exited with {completed.returncode}"
    return completed.stdout.strip(), warning


def provider_config(args: argparse.Namespace) -> tuple[str, str, str]:
    provider = args.provider.lower()
    if provider == "deepseek":
        api_key = args.api_key or os.getenv("DEEPSEEK_API_KEY")
        base_url = args.base_url or os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
        model = args.model or os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
    elif provider == "reasonix":
        api_key = args.api_key or os.getenv("REASONIX_API_KEY")
        base_url = args.base_url or os.getenv("REASONIX_BASE_URL")
        model = args.model or os.getenv("REASONIX_MODEL", "deepseek-chat")
    else:
        env_name = args.api_key_env or "OPENAI_API_KEY"
        api_key = args.api_key or os.getenv(env_name)
        base_url = args.base_url
        model = args.model

    missing = []
    if not api_key:
        missing.append("api key")
    if not base_url:
        missing.append("base url")
    if not model:
        missing.append("model")
    if missing:
        raise SystemExit(f"Missing {', '.join(missing)} for provider '{provider}'.")
    return api_key, base_url.rstrip("/"), model


def chat_completion_url(base_url: str) -> str:
    if base_url.endswith("/chat/completions"):
        return base_url
    return f"{base_url}/chat/completions"


def ask_model(args: argparse.Namespace, evidence: dict) -> str:
    api_key, base_url, model = provider_config(args)
    question = args.question or "Analyze the image evidence and summarize the important content."
    system = (
        "You analyze images indirectly from OCR text and metadata. "
        "Be explicit about uncertainty and do not pretend you saw pixels."
    )
    user = {
        "question": question,
        "image_metadata": evidence["metadata"],
        "ocr_text": evidence["ocr_text"],
        "ocr_warning": evidence.get("ocr_warning"),
        "operator_notes": args.notes or "",
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": json.dumps(user, ensure_ascii=False, indent=2)},
        ],
        "temperature": args.temperature,
    }
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        chat_completion_url(base_url),
        data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=args.timeout) as response:
            body = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"Model request failed: HTTP {exc.code}\n{detail}") from exc
    except Exception as exc:
        raise SystemExit(f"Model request failed: {exc}") from exc

    try:
        return body["choices"][0]["message"]["content"]
    except Exception:
        return json.dumps(body, ensure_ascii=False, indent=2)


def render_markdown(evidence: dict) -> str:
    metadata = evidence["metadata"]
    lines = [
        "# Image OCR Evidence",
        "",
        "## Metadata",
        "",
    ]
    for key, value in metadata.items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## OCR Text", "", evidence["ocr_text"] or "[No OCR text extracted]"])
    if evidence.get("ocr_warning"):
        lines.extend(["", "## OCR Warning", "", evidence["ocr_warning"]])
    if evidence.get("model_response"):
        lines.extend(["", "## Model Response", "", evidence["model_response"]])
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", help="Path to an image file")
    parser.add_argument("--lang", default="eng", help="Tesseract language, e.g. eng or chi_sim+eng")
    parser.add_argument("--psm", default="6", help="Tesseract page segmentation mode")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    parser.add_argument("--ask", action="store_true", help="Send OCR evidence to a text model")
    parser.add_argument("--question", help="Question for the model")
    parser.add_argument("--notes", help="Additional visual notes from Codex or the user")
    parser.add_argument("--provider", default="deepseek", choices=["deepseek", "reasonix", "custom"])
    parser.add_argument("--base-url", help="OpenAI-compatible base URL or /chat/completions URL")
    parser.add_argument("--model", help="Model name")
    parser.add_argument("--api-key", help="API key value; prefer env vars for normal use")
    parser.add_argument("--api-key-env", help="Env var for custom provider API key")
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--timeout", type=int, default=60)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    path = Path(args.image).expanduser().resolve()
    if not path.exists():
        raise SystemExit(f"Image not found: {path}")

    ocr_text, ocr_warning = run_tesseract(path, args.lang, args.psm)
    evidence = {
        "metadata": image_metadata(path),
        "ocr_text": ocr_text,
        "ocr_warning": ocr_warning,
    }
    if args.ask:
        evidence["model_response"] = ask_model(args, evidence)

    if args.format == "json":
        print(json.dumps(evidence, ensure_ascii=False, indent=2))
    else:
        print(render_markdown(evidence))
    return 0


if __name__ == "__main__":
    sys.exit(main())
