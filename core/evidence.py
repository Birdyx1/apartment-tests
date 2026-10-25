SENSITIVE_KEYWORDS = (
    "password",
    "token",
    "captcha",
    "authorization",
    "secret",
)

REDACTED = "[REDACTED]"


def sanitize(value):
    """递归复制字典和列表，并隐藏敏感字段的值。"""
    if isinstance(value, dict):
        safe_data = {}

        for key, item in value.items():
            key_name = str(key).lower()

            if any(word in key_name for word in SENSITIVE_KEYWORDS):
                safe_data[key] = REDACTED
            else:
                safe_data[key] = sanitize(item)

        return safe_data

    if isinstance(value, list):
        return [sanitize(item) for item in value]

    return value