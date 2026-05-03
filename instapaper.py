from __future__ import annotations

import requests

# Uses the Instapaper Simple API (HTTP Basic Auth), not the OAuth Full API.
# Docs: https://www.instapaper.com/api/simple
# POST /api/add — returns 201 on success, 400 if the URL is invalid or already saved.


class InstapaperError(RuntimeError):
    pass


class RetryableInstapaperError(InstapaperError):
    pass


class InstapaperClient:
    def __init__(self, username: str, password: str, timeout_seconds: int = 30):
        self.username = username
        self.password = password
        self.timeout_seconds = timeout_seconds

    def add_bookmark(self, *, url: str, title: str | None = None) -> None:
        r = requests.post(
            "https://www.instapaper.com/api/add",
            data={
                "url": url,
                "title": title,
                "selection": "",
            },
            auth=(self.username, self.password),
            timeout=self.timeout_seconds,
        )

        # 400 "already" means Instapaper already has this URL — treat as success.
        if r.status_code == 400 and "already" in r.text.lower():
            return

        if r.status_code == 201:
            return

        if r.status_code in (500, 502, 503, 504, 429):
            raise RetryableInstapaperError(r.text)

        raise InstapaperError(f"{r.status_code}: {r.text}")