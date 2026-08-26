"""Detection of password values in fetched response content."""

from __future__ import annotations

import re


PASSWORD_RE = re.compile(r"VISUALPING\{[0-9a-fA-F]{16}\}")
EXAMPLE_PASSWORD = "VISUALPING{0000deadbeef0000}"


def find_passwords(content: str) -> set[str]:
    """Return all unique password-format matches in content."""
    return {
        password
        for password in PASSWORD_RE.findall(content)
        if password != EXAMPLE_PASSWORD
    }


def find_passwords_in_response(
    url: str,
    headers: dict[str, str],
    body: bytes | str,
) -> set[str]:
    """Scan all text-bearing parts of a response for password values."""
    if isinstance(body, bytes):
        body_text = body.decode("latin-1")
    else:
        body_text = body
    values = find_passwords(url)
    values.update(find_passwords("\n".join(headers.values())))
    values.update(find_passwords(body_text))
    return values