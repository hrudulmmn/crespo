import re

SECRET_PATTERNS = [
    r'(?i)(api[_-]?key\s*[:=]\s*["\'])([^"\']+)(["\'])',
    r'(?i)(secret\s*[:=]\s*["\'])([^"\']+)(["\'])',
    r'(?i)(token\s*[:=]\s*["\'])([^"\']+)(["\'])',
    r'(?i)(password\s*[:=]\s*["\'])([^"\']+)(["\'])',
]

def redact(text: str) -> str:
    for pattern in SECRET_PATTERNS:
        text = re.sub(
            pattern,
            r'\1[REDACTED]\3',
            text
        )
    return text