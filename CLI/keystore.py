import os
from pathlib import Path

CONFIG_DIR  = Path.home() / ".crespo"
CONFIG_FILE = CONFIG_DIR / "config"


def save_key(value: str) -> None:
    CONFIG_DIR.mkdir(exist_ok=True)
    CONFIG_FILE.write_text(f"CRESPO_GROQ_KEY={value}\n")
    try:
        CONFIG_FILE.chmod(0o600)
    except Exception:
        pass


def load_key() -> str | None:
    """Load from config file."""
    if not CONFIG_FILE.exists():
        return None
    for line in CONFIG_FILE.read_text().splitlines():
        if line.startswith("CRESPO_GROQ_KEY="):
            return line.split("=", 1)[1].strip()
    return None


def get_key(provided: str | None = None) -> str | None:
    """
    Priority:
    1. --groq flag (provided argument)
    2. CRESPO_GROQ_KEY already in system environment
    3. Saved in ~/.crespo/config

    If new key provided and differs from saved — update config.
    Always sets os.environ so summarise.py can access it directly.
    """
    saved_key = load_key()

    # resolve which key to use
    if provided:
        if provided != saved_key:
            save_key(provided)  # new key — save it
        key = provided

    elif os.environ.get("CRESPO_GROQ_KEY"):
        # already in system environment
        key = os.environ["CRESPO_GROQ_KEY"]

    elif saved_key:
        key = saved_key

    else:
        return None  # no key found anywhere

    # always inject into os.environ
    # so summarise.py can just do os.environ.get("CRESPO_GROQ_KEY")
    os.environ["CRESPO_GROQ_KEY"] = key
    return key