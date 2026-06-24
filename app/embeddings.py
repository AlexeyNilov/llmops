import re
from typing import Any, AsyncGenerator

import aiofiles

from lmstudio import embeddings_client

DEFAULT_CHUNK_SIZE = 1024  # characters
EMBEDDING_MODEL = "v5-small-retrieval-Q8_0.gguf"


async def load(
    filepath: str, chunk_size: int = DEFAULT_CHUNK_SIZE
) -> AsyncGenerator[str, Any]:
    async with aiofiles.open(filepath, "r", encoding="utf-8") as f:
        while chunk := await f.read(chunk_size):
            yield chunk


def clean(text: str) -> str:
    t = text.replace("\n", " ")
    t = re.sub(r"\s+", " ", t)
    t = re.sub(r"\. ,", "", t)
    t = t.replace("..", ".")
    t = t.replace(". .", ".")
    cleaned_text = t.replace("\n", " ").strip()
    return cleaned_text


async def embed(text: str) -> list[float]:
    response = await embeddings_client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text,
    )
    return response.data[0].embedding


async def embed_many(texts: list[str]) -> list[list[float]]:
    response = await embeddings_client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=texts,
    )
    return [item.embedding for item in response.data]
