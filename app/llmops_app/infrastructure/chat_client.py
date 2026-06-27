from openai import AsyncOpenAI

from llmops_app.config import LM_STUDIO_API_KEY, LM_STUDIO_CHAT_BASE_URL

chat_client = AsyncOpenAI(
    api_key=LM_STUDIO_API_KEY,
    base_url=LM_STUDIO_CHAT_BASE_URL,
)
