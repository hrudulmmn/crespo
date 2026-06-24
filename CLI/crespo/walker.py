import os
from pathlib import Path
import fnmatch
from . import config
import sys

HAS_UI = False 

try:
    from . import cli
    HAS_UI = True
except ImportError:
    HAS_UI = False

IGNORE_FOLDERS = {
    ".git", ".github",
    ".venv", "venv",
    "node_modules", "__pycache__",
    ".pytest_cache", ".mypy_cache",
    ".tox", ".next",
    "dist", "build", "target",
    "site-packages",
    ".idea", ".vscode",
    "docs", "doc",
    "examples", "example",
    "scripts",
    "spec", "specs",
    "e2e", "integration",
    "fixtures", "mocks",
    "testing", "testdata",
    "coverage", "htmlcov",
    "vendor","docs_src"
}

IGNORE_PREFIXES = (
    "test", "__test", "__mock", ".cache",
)

IGNORE_SUFFIXES = (
    "_test", "_tests", "_spec",
    "_specs", "_mock", "_mocks",
)

IGNORE_FILES = {
    'package-lock.json', 'yarn.lock',
    '.DS_Store', '.gitignore', '.env',
    'poetry.lock', 'Pipfile.lock',
}

CONFIG_FILES = {
    "package.json", "requirements.txt",
    "Cargo.toml", "go.mod", "Dockerfile"
}


def should_ignore_file(filename: str) -> bool:
    stem = Path(filename).stem.lower()
    name = filename.lower()
    if stem.startswith("test_"):        return True
    if stem.endswith("_test"):          return True
    if name.endswith(".test.js"):       return True
    if name.endswith(".test.ts"):       return True
    if name.endswith(".spec.js"):       return True
    if name.endswith(".spec.ts"):       return True
    if name.endswith(".test.jsx"):      return True
    if name.endswith(".test.tsx"):      return True
    if stem in {
        "conftest", "jest.config",
        "vitest.config", "pytest.ini",
        "setup.cfg", "tox.ini"
    }:
        return True
    return False

def walk_error(err):
    cli.print_info(f"Skipping {err.filename}:{err.strerror}")


def _load_gitignore_patterns(base_path: Path) -> list[str]:
    patterns = []
    for root, dirs, files in os.walk(base_path):
        if ".gitignore" in files:
            gitignore = Path(root) / ".gitignore"
            rel_root = Path(root).relative_to(base_path)
            try:
                for line in gitignore.read_text(
                    encoding="utf8", errors="ignore"
                ).splitlines():
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if str(rel_root) != ".":
                        patterns.append(str(rel_root / line))
                    else:
                        patterns.append(line)
            except Exception:
                pass
        dirs[:] = [d for d in dirs if not d.startswith(".")]
    return patterns


def _is_gitignored(rel_path: str, patterns: list[str]) -> bool:
    rel = rel_path.replace("\\", "/")
    parts = Path(rel).parts
    for pattern in patterns:
        if pattern.startswith("!"):
            continue  # negation not implemented — v2
        pat = pattern.rstrip("/").replace("\\", "/")
        candidates = [rel]
        for i in range(len(parts)):
            candidates.append("/".join(parts[i:]))
        for candidate in candidates:
            if fnmatch.fnmatch(candidate, pat):
                return True
            if fnmatch.fnmatch(Path(candidate).name, pat):
                return True
    return False


def walk_dir(path: str, respect_gitignore: bool = True):
    if not os.path.isdir(path):
        cli.print_error("Not a Directory!")
        sys.exit(1)
    base_path = Path(path).resolve()
    gitignore_patterns = (
        _load_gitignore_patterns(base_path)
        if respect_gitignore else []
    )

    if HAS_UI:
        print(f"\n Walking: {cli._clickable(str(base_path))}\n")
    else:
        print(f"\n Walking: {str(base_path)}\n")
    valid_files = []


    for root, dirs, files in os.walk(base_path,followlinks=False,onerror=walk_error,topdown=True):
        try:
            rel_root = str(
                Path(root).resolve().relative_to(base_path)
            )
        except ValueError:
            cli.print_error(f"Skipping file outside repo: {full_path}")
            continue

        dirs[:] = [
            d for d in dirs
            if d not in IGNORE_FOLDERS
            and not d.startswith(".")
            and not d.lower().startswith(IGNORE_PREFIXES)
            and not d.lower().endswith(IGNORE_SUFFIXES)
            and not _is_gitignored(
                str(Path(rel_root) / d)
                if rel_root != "." else d,
                gitignore_patterns
            )
        ]

        for file in files:
            if file in IGNORE_FILES:
                continue
            if file.startswith(".env"):
                continue
            if should_ignore_file(file):
                continue

            full_path = os.path.join(root, file)

            try:
                rel_path = str(
                    Path(full_path).resolve()
                    .relative_to(base_path)
                )
            except ValueError:
                cli.print_error(f"Skipping file outside repo: {full_path}")
                continue

            if respect_gitignore and _is_gitignored(
                rel_path, gitignore_patterns
            ):
                continue

            isconfig = file in CONFIG_FILES
            if not isconfig and \
            Path(file).suffix.lower() not in config.get_config():
                continue

            valid_files.append({
                "abspath":  full_path,
                "relpath":  rel_path,
                "isconfig": isconfig,
                "ext":      Path(file).suffix.lower(),
                "lang":     Path(file).suffix.lower().replace(".", ""),
            })

    return valid_files