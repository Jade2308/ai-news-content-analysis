import os
import sys

import requests
from dotenv import load_dotenv


def _safe_print(text: str) -> None:
    """Print text without crashing on legacy terminal encodings."""
    encoding = sys.stdout.encoding or "utf-8"
    sys.stdout.buffer.write((text + "\n").encode(encoding, errors="replace"))


def main() -> int:
    load_dotenv()
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        _safe_print("GEMINI_API_KEY not found in .env file.")
        return 1

    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    resp = requests.get(url, timeout=30)

    if resp.status_code == 200:
        models = resp.json().get("models", [])
        _safe_print("=== GOOGLE MODELS WITH generateContent SUPPORT ===")
        for model in models:
            name = model.get("name")
            methods = model.get("supportedGenerationMethods", [])
            if "generateContent" in methods:
                _safe_print(f"- {name}")
        _safe_print("=================================================")
        return 0

    _safe_print(f"Error: {resp.status_code} - {resp.text}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
