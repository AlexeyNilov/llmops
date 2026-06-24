# main.py

from loguru import logger
import time
from uuid import uuid4
from typing import Awaitable, Callable
from fastapi import FastAPI, Request, Response, Depends
from models import generate_text
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
async def serve_language_model_controller(prompt: str, rag_content: str = Depends(get_rag_content)) -> str:
    prompt = "Answer this question: '" + prompt + "' based on this content: " + rag_content
    logger.info(prompt)
    output = await generate_text(prompt)
    return output
