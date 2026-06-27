import re
from typing import Any, AsyncGenerator

import aiofiles

DEFAULT_CHUNK_SIZE = 1024  # characters


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
