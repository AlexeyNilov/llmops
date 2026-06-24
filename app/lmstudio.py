from openai import AsyncOpenAI

LM_STUDIO_CHAT_BASE_URL = "http://127.0.0.1:12345/v1"
LM_STUDIO_EMBEDDINGS_BASE_URL = "http://127.0.0.1:12346/v1"
LM_STUDIO_API_KEY = "key"

chat_client = AsyncOpenAI(
    api_key=LM_STUDIO_API_KEY,
    base_url=LM_STUDIO_CHAT_BASE_URL,
)

embeddings_client = AsyncOpenAI(
    api_key=LM_STUDIO_API_KEY,
    base_url=LM_STUDIO_EMBEDDINGS_BASE_URL,
)
