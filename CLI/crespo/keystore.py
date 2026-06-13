import os
from pathlib import Path

CONFIG_DIR  = Path.home() / ".crespo"
CONFIG_FILE = CONFIG_DIR / "config"


def save_key(value: str) -> None:
    try:
        CONFIG_DIR.mkdir(exist_ok=True)
        CONFIG_FILE.write_text(f"CRESPO_GROQ_KEY={value}\n", encoding="utf-8")
        CONFIG_FILE.chmod(0o600)
    except Exception:
        pass  # saving is best-effort; key still works via os.environ


def load_key() -> str | None:
    if not CONFIG_FILE.exists():
        return None
    try:
        for line in CONFIG_FILE.read_text(encoding="utf-8").splitlines():
            if line.startswith("CRESPO_GROQ_KEY="):
                return line.split("=", 1)[1].strip() or None
    except Exception:
        return None
    return None


def get_key(provided: str | None = None) -> str | None:
    if provided:
        provided = provided.strip()
        if not provided:
            return None

    saved_key = load_key()

    if provided:
        if provided != saved_key:
            save_key(provided)
        key = provided
    elif os.environ.get("CRESPO_GROQ_KEY", "").strip():
        key = os.environ["CRESPO_GROQ_KEY"].strip()
    elif saved_key:
        key = saved_key
    else:
        return None

    os.environ["CRESPO_GROQ_KEY"] = key
    return key