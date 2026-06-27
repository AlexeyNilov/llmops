from collections.abc import AsyncIterator

from lmstudio import chat_client

CHAT_MODEL = "gemma-4-12b"


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
