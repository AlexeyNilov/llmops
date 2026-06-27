from collections.abc import AsyncIterator

from llmops.config import CHAT_MODEL
from llmops.infrastructure.chat_client import chat_client


async def stream_text(prompt: str) -> AsyncIterator[str]:
    stream = await chat_client.chat.completions.create(
        model=CHAT_MODEL,
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ],
        stream=True,
    )

    async for chunk in stream:
        content = chunk.choices[0].delta.content
        if content:
            yield content
