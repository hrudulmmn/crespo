import os
from pathlib import Path
import fnmatch
import config


def _load_gitignore_patterns(base_path: Path) -> list[str]:
    """
    Load all .gitignore files from base_path downward.
    Returns a flat list of patterns (relative to base_path).
    """
    patterns = []
    for root, dirs, files in os.walk(base_path):
        if ".gitignore" in files:
            gitignore = Path(root) / ".gitignore"
            rel_root = Path(root).relative_to(base_path)
            try:
                for line in gitignore.read_text(encoding="utf8", errors="ignore").splitlines():
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    # prefix non-root patterns with their subdirectory
                    if str(rel_root) != ".":
                        patterns.append(str(rel_root / line))
                    else:
                        patterns.append(line)
            except Exception:
                pass
        # don't descend into ignored folders
        dirs[:] = [d for d in dirs if not d.startswith(".")]
    return patterns


def _is_gitignored(rel_path: str, patterns: list[str]) -> bool:
    """
    Return True if rel_path matches any gitignore pattern.
    Handles directory patterns (trailing /), wildcards, and negation (!).
    """
    rel = rel_path.replace("\\", "/")
    parts = Path(rel).parts

    for pattern in patterns:
        # negation — never ignore
        if pattern.startswith("!"):
            continue

        pat = pattern.rstrip("/")
        pat_unix = pat.replace("\\", "/")

        # match against full path and each suffix (so node_modules matches anywhere)
        candidates = [rel]
        for i in range(len(parts)):
            candidates.append("/".join(parts[i:]))

        for candidate in candidates:
            if fnmatch.fnmatch(candidate, pat_unix):
                return True
            # also match just the filename
            if fnmatch.fnmatch(Path(candidate).name, pat_unix):
                return True

    return False


def walk_dir(path: str, respect_gitignore: bool = True):
    IGNORE_FOLDERS = {
        ".git", ".github", ".venv", "venv", "node_modules",
        "__pycache__", ".pytest_cache", ".mypy_cache", ".tox",
        ".next", "dist", "build", "target", "site-packages",
        ".idea", ".vscode",
    }
    IGNORE_FILES = {
        "package-lock.json", "yarn.lock", ".DS_Store", ".gitignore", ".env"
    }
    CONFIG_FILES = {
        "package.json", "requirements.txt", "Cargo.toml", "go.mod", "Dockerfile"
    }

    base_path = Path(path).resolve()
    gitignore_patterns = _load_gitignore_patterns(base_path) if respect_gitignore else []

    print(f"\n Walking Directory: {path}\n")

    valid_files = []

    for root, dirs, files in os.walk(path):
        rel_root = str(Path(root).resolve().relative_to(base_path))

        # filter dirs in-place
        dirs[:] = [
            d for d in dirs
            if d not in IGNORE_FOLDERS
            and not d.startswith(".")
            and not d.startswith("_")
            and not _is_gitignored(
                str(Path(rel_root) / d) if rel_root != "." else d,
                gitignore_patterns
            )
        ]

        for file in files:
            if file in IGNORE_FILES:
                continue
            if file.startswith(".env"):
                continue

            full_path = os.path.join(root, file)
            rel_path = str(Path(full_path).resolve().relative_to(base_path))

            # check gitignore
            if respect_gitignore and _is_gitignored(rel_path, gitignore_patterns):
                continue

            isconfig = file in CONFIG_FILES
            if not isconfig and Path(file).suffix.lower() not in config.get_config():
                continue

            valid_files.append({
                "abspath":  full_path,
                "relpath":  rel_path,
                "isconfig": isconfig,
                "ext":      Path(file).suffix.lower(),
            })

    return valid_files