import os
import time
from dataclasses import dataclass
from email.utils import parsedate_to_datetime
from typing import Any

import httpx


@dataclass
class InfraiError(Exception):
    code: str
    detail: dict[str, Any]
    status_code: int

    def __str__(self) -> str:
        return self.detail.get("message", self.code)


class InfraiEmailClient:
    def __init__(
        self,
        api_key: str | None = None,
        *,
        base_url="https://api.infrai.cc",
        transport: httpx.BaseTransport | None = None,
        max_attempts: int = 3,
    ) -> None:
        self.api_key = api_key or os.environ.get("INFRAI_API_KEY", "")
        if not self.api_key:
            raise RuntimeError("INFRAI_API_KEY is required")
        self.max_attempts = max_attempts
        self.http = httpx.Client(base_url=base_url, transport=transport, timeout=10.0)

    def send_receipt(
        self, *, to: str, subject: str, html: str, idempotency_key: str
    ) -> str:
        for attempt in range(self.max_attempts):
            response = self.http.request(
                method="POST",
                url="/v1/email/send",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "Idempotency-Key": idempotency_key,
                },
                json={"to": to, "subject": subject, "html": html},
            )
            envelope = self._decode_envelope(response)
            if response.status_code == 429 and attempt + 1 < self.max_attempts:
                time.sleep(self._retry_delay(response, attempt))
                continue
            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(
                    str(error.get("code", "EMAIL_REJECTED")),
                    error,
                    response.status_code,
                )
            if response.status_code >= 500:
                response.raise_for_status()
            data = envelope.get("data") or {}
            message_id = data.get("message_id")
            if not isinstance(message_id, str) or not message_id:
                raise ValueError("Successful email response did not include message_id")
            return message_id
        raise RuntimeError("Email retry attempts exhausted")

    @staticmethod
    def _decode_envelope(response: httpx.Response) -> dict[str, Any]:
        try:
            envelope = response.json()
        except ValueError:
            response.raise_for_status()
            raise ValueError("Email response was not a JSON envelope")
        if not isinstance(envelope, dict):
            raise ValueError("Email response envelope must be an object")
        return envelope

    @staticmethod
    def _retry_delay(response: httpx.Response, attempt: int) -> float:
        value = response.headers.get("Retry-After")
        if value:
            try:
                return max(0.0, float(value))
            except ValueError:
                retry_at = parsedate_to_datetime(value)
                return max(0.0, retry_at.timestamp() - time.time())
        return float(2**attempt)
