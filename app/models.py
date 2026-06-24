from lmstudio import chat_client

CHAT_MODEL = "gemma-4-12b"


async def generate_text(prompt: str) -> str:
    response = await chat_client.chat.completions.create(
        model=CHAT_MODEL,
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ],
    )
    return response.choices[0].message.content.strip()
