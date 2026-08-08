from __future__ import annotations

from collections.abc import Mapping
from time import monotonic, sleep
from typing import Any, Self

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential


class RetriableStatusError(httpx.HTTPStatusError):
    pass


class JsonApiClient:
    def __init__(
        self,
        *,
        base_url: str,
        headers: Mapping[str, str] | None = None,
        timeout: float = 45,
        min_interval_seconds: float = 0,
        client: httpx.Client | None = None,
    ) -> None:
        self._owned_client = client is None
        self.min_interval_seconds = min_interval_seconds
        self._last_request_at: float | None = None
        self.client = client or httpx.Client(
            base_url=base_url,
            follow_redirects=True,
            timeout=timeout,
            headers=dict(headers or {}),
        )

    def close(self) -> None:
        if self._owned_client:
            self.client.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    @retry(
        retry=retry_if_exception_type((httpx.TransportError, RetriableStatusError)),
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=1, max=16),
        reraise=True,
    )
    def get_json(self, path: str, *, params: Mapping[str, Any] | None = None) -> dict[str, Any]:
        if self._last_request_at is not None:
            remaining = self.min_interval_seconds - (monotonic() - self._last_request_at)
            if remaining > 0:
                sleep(remaining)
        response = self.client.get(path, params=params)
        self._last_request_at = monotonic()
        if response.status_code == 429 or response.status_code >= 500:
            raise RetriableStatusError(
                "retriable provider response", request=response.request, response=response
            )
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise TypeError("provider returned a non-object JSON response")
        return payload

    def get_optional_json(
        self, path: str, *, params: Mapping[str, Any] | None = None
    ) -> dict[str, Any] | None:
        try:
            return self.get_json(path, params=params)
        except httpx.HTTPStatusError as error:
            if error.response.status_code == 404:
                return None
            raise
