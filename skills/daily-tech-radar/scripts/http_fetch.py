"""Shared HTTP fetch helpers for Daily Tech Radar (stdlib only)."""

from __future__ import annotations

import ssl
import time
import urllib.error
import urllib.request
from typing import Optional


DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (compatible; DailyTechRadar/0.2; +https://github.com/poirotw66/Daily-Tech-Radar)"
)


def ssl_context(insecure_skip_tls_verify: bool) -> ssl.SSLContext:
    if insecure_skip_tls_verify:
        return ssl._create_unverified_context()
    return ssl.create_default_context()


def fetch_bytes(
    url: str,
    *,
    timeout: int = 60,
    insecure_skip_tls_verify: bool = False,
    max_retries: int = 3,
    retry_delay_seconds: float = 2.0,
    user_agent: str = DEFAULT_USER_AGENT,
) -> tuple[Optional[bytes], Optional[str]]:
    """Return (body, error_message). error_message is set when all retries fail."""
    last_error: Optional[str] = None
    for attempt in range(1, max_retries + 1):
        try:
            request = urllib.request.Request(
                url,
                headers={
                    "User-Agent": user_agent,
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.9",
                },
            )
            context = ssl_context(insecure_skip_tls_verify)
            with urllib.request.urlopen(request, timeout=timeout, context=context) as response:
                return response.read(), None
        except (urllib.error.URLError, TimeoutError, ssl.SSLError, OSError) as exc:
            last_error = str(exc)
            if attempt < max_retries:
                time.sleep(retry_delay_seconds * attempt)
    return None, last_error
