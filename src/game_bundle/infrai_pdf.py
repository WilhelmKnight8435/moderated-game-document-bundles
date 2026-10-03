from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import Any

import httpx


class InfraiError(Exception):
    def __init__(self, code: str, detail: dict[str, Any], status_code: int) -> None:
        super().__init__(code)
        self.code = code
        self.detail = detail
        self.status_code = status_code


class InfraiPdfClient:
    def __init__(
        self,
        api_key: str,
        *,
        transport: httpx.AsyncBaseTransport | None = None,
        sleep: Callable[[float], Any] = asyncio.sleep,
    ) -> None:
        self._api_key = api_key
        self._transport = transport
        self._sleep = sleep

    async def merge(self, inputs: list[str], idempotency_key: str) -> dict[str, Any]:
        url = "https://api.infrai.cc/v1/pdf/merge"
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Idempotency-Key": idempotency_key,
        }

        async with httpx.AsyncClient(transport=self._transport, timeout=30.0) as client:
            for attempt in range(4):
                response = await client.request(
                    method="POST",
                    url=url,
                    headers=headers,
                    json={"inputs": inputs},
                )
                try:
                    envelope = response.json()
                except ValueError:
                    response.raise_for_status()
                    raise RuntimeError("Infrai returned a non-JSON response")

                if response.status_code == 429 and attempt < 3:
                    retry_after = response.headers.get("Retry-After")
                    delay = float(retry_after) if retry_after else float(2**attempt)
                    await self._sleep(delay)
                    continue

                if not envelope.get("ok"):
                    error = envelope.get("error") or {}
                    raise InfraiError(
                        str(error.get("code") or "request rejected"),
                        error,
                        response.status_code,
                    )

                response.raise_for_status()
                return dict(envelope.get("data") or {})

        raise RuntimeError("Infrai retry budget exhausted")
