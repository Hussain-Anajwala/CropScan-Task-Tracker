"""Advisory API router."""

from __future__ import annotations

import json

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sse_starlette.sse import EventSourceResponse

from backend.schemas import AdvisoryRequest, AdvisoryResponse
from backend.services.advisory_chain import generate_full_advisory, stream_advisory


router = APIRouter(prefix="/advisory", tags=["advisory"])


@router.post("")
async def advisory(request: AdvisoryRequest) -> JSONResponse:
    """Return a structured advisory JSON payload."""
    response = await generate_full_advisory(
        image_b64=request.image,
        disease=request.disease,
        crop=request.crop,
        confidence=request.confidence,
        language=request.language,
    )
    return JSONResponse(content=response.model_dump())


@router.post("/stream")
async def advisory_stream(request: AdvisoryRequest) -> EventSourceResponse:
    """Optional SSE stream for advisory token updates."""
    async def event_generator():
        collected_tokens: list[str] = []
        async for token in stream_advisory(
            image_b64=request.image,
            disease=request.disease,
            crop=request.crop,
            confidence=request.confidence,
        ):
            collected_tokens.append(token)
            yield {
                "event": "token",
                "data": json.dumps({"token": token}),
            }

        final_advisory = await generate_full_advisory(
            image_b64=request.image,
            disease=request.disease,
            crop=request.crop,
            confidence=request.confidence,
            language=request.language,
        )
        yield {
            "event": "final",
            "data": json.dumps({"done": True, "full_advisory": final_advisory.model_dump()}),
        }

    return EventSourceResponse(event_generator())
