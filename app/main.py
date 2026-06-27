# main.py

import time
from collections.abc import Awaitable, Callable
from uuid import uuid4

from fastapi import Depends, FastAPI, Request, Response
from fastapi.responses import StreamingResponse
from loguru import logger
from models import stream_text
from service import get_rag_content

app = FastAPI()


@app.middleware("http")
async def monitor_service(
    req: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    request_id = uuid4().hex
    start_time = time.perf_counter()
    response: Response = await call_next(req)
    response_time = round(time.perf_counter() - start_time, 4)
    response.headers["X-Response-Time"] = str(response_time)
    response.headers["X-API-Request-ID"] = request_id
    logger.info(response.headers)
    return response


@app.get("/generate/text")
async def serve_language_model_controller(
    prompt: str, rag_content: str = Depends(get_rag_content)
) -> StreamingResponse:
    prompt = "Answer this question: '" + prompt + "' based on this content: " + rag_content
    logger.info(prompt)
    return StreamingResponse(stream_text(prompt), media_type="text/plain")
