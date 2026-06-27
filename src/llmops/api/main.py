import time
from collections.abc import Awaitable, Callable
from uuid import uuid4

from fastapi import Depends, FastAPI, Request, Response
from fastapi.responses import StreamingResponse
from loguru import logger

from llmops.infrastructure.language_model import stream_text
from llmops.use_cases.answer_question import (
    AnswerContext,
    build_answer_prompt,
    get_answer_context,
)

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
    prompt: str,
    answer_context: AnswerContext = Depends(get_answer_context),
) -> StreamingResponse:
    answer_prompt = build_answer_prompt(prompt, answer_context)
    logger.info(
        {
            "event": "generate_text",
            "prompt_length": len(prompt),
            "rag_content_length": len(answer_context.rag_content),
            "graph_content_length": len(answer_context.graph_content),
        }
    )
    return StreamingResponse(stream_text(answer_prompt), media_type="text/plain")
