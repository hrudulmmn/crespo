import re

SECRET_PATTERNS = [
    # quoted assignments: api_key = "abc", token: 'xyz'
    r'(?i)(api[_-]?key\s*[:=]\s*["\'])([^"\']{8,})(["\'])',
    r'(?i)(secret\s*[:=]\s*["\'])([^"\']{8,})(["\'])',
    r'(?i)(token\s*[:=]\s*["\'])([^"\']{8,})(["\'])',
    r'(?i)(password\s*[:=]\s*["\'])([^"\']{8,})(["\'])',
    r'(?i)(auth\s*[:=]\s*["\'])([^"\']{8,})(["\'])',

    # unquoted .env style: KEY=rawvalue
    r'(?i)^(\s*[A-Z][A-Z0-9_]*(?:KEY|SECRET|TOKEN|PASSWORD|AUTH)\s*=\s*)([^\s"\'#]{8,})',

    # known key prefixes by pattern
    r'(gsk_[a-zA-Z0-9]{20,})',       # Groq
    r'(sk-ant-[a-zA-Z0-9\-]{20,})',  # Anthropic
    r'(sk-[a-zA-Z0-9]{20,})',        # OpenAI
    r'(ghp_[a-zA-Z0-9]{20,})',       # GitHub personal token
    r'(xox[baprs]-[a-zA-Z0-9\-]+)',  # Slack
    r'(AKIA[A-Z0-9]{16})',           # AWS access key
]

REDACTED = "[REDACTED]"

def redact(text: str) -> str:
    for pattern in SECRET_PATTERNS:
        # patterns with capture groups: replace group 2
        try:
            compiled = re.compile(pattern, re.MULTILINE)
            if compiled.groups == 1:
                # full match is the secret
                text = compiled.sub(REDACTED, text)
            else:
                text = compiled.sub(lambda m: m.group(1) + REDACTED + (m.group(3) if compiled.groups >= 3 else ""), text)
        except Exception:
            continue
    return text