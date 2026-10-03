from __future__ import annotations

import os

from fastapi import FastAPI, HTTPException

from .infrai_pdf import InfraiError, InfraiPdfClient
from .moderation_bundle import BundleRequest, BundleResult, build_event_bundles

app = FastAPI(title="Game document bundle service")


@app.post("/bundles/resolve", response_model=BundleResult)
async def resolve_bundle(request: BundleRequest) -> BundleResult:
    api_key = os.environ.get("INFRAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=503, detail="INFRAI_API_KEY is required")

    try:
        return await build_event_bundles(request, InfraiPdfClient(api_key))
    except InfraiError as exc:
        client_status = exc.status_code if 400 <= exc.status_code < 500 else 502
        raise HTTPException(
            status_code=client_status,
            detail={"code": exc.code, "error": exc.detail},
        ) from exc
