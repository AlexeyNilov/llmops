import os
from typing import Any

import httpx
from llama_index.core.base.embeddings.base import BaseEmbedding, Embedding
from llama_index.core.bridge.pydantic import Field
from llama_index.core.callbacks.base import CallbackManager
from qdrant_client import QdrantClient
from qdrant_client.http import models

DEFAULT_QDRANT_URL = "http://localhost:6333"
DEFAULT_EMBEDDINGS_BASE_URL = "http://127.0.0.1:12346"
DEFAULT_EMBEDDING_MODEL = "v5-small-retrieval-Q8_0.gguf"

DEFAULT_COLLECTION_NAME = os.getenv(
    "QDRANT_COLLECTION_NAME",
    "knowledgebase",
)
QDRANT_URL = os.getenv("QDRANT_URL", DEFAULT_QDRANT_URL)
EMBEDDINGS_BASE_URL = os.getenv(
    "LLAMAINDEX_EMBEDDINGS_BASE_URL",
    os.getenv("EMBEDDINGS_BASE_URL", DEFAULT_EMBEDDINGS_BASE_URL),
)
EMBEDDING_PROVIDER = os.getenv("LLAMAINDEX_EMBEDDING_PROVIDER", "llamafile")
EMBEDDING_MODEL = os.getenv("LLAMAINDEX_EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL)
RETRIEVAL_TOP_K = int(os.getenv("RAG_RETRIEVAL_TOP_K", "2"))


class LlamaCppServerEmbedding(BaseEmbedding):
    """LlamaIndex adapter for llama.cpp's OpenAI-compatible embeddings API."""

    base_url: str = Field(description="Base URL for the llama.cpp server")
    model: str = Field(description="Embedding model name")
    request_timeout: float = Field(default=30.0)

    def __init__(
        self,
        base_url: str,
        model: str,
        callback_manager: CallbackManager | None = None,
        **kwargs: Any,
    ) -> None:
        init_kwargs: dict[str, Any] = {
            "base_url": base_url.rstrip("/"),
            "model": model,
            "callback_manager": callback_manager or CallbackManager([]),
        }
        init_kwargs.update(kwargs)
        super().__init__(**init_kwargs)

    @classmethod
    def class_name(cls) -> str:
        return "LlamaCppServerEmbedding"

    def _embedding_payload(self, text_or_texts: str | list[str]) -> dict[str, Any]:
        return {
            "model": self.model,
            "input": text_or_texts,
        }

    def _parse_embeddings(self, response_json: dict[str, Any]) -> list[Embedding]:
        data = sorted(response_json["data"], key=lambda item: item["index"])
        return [item["embedding"] for item in data]

    def _get_query_embedding(self, query: str) -> Embedding:
        return self._get_text_embedding(query)

    async def _aget_query_embedding(self, query: str) -> Embedding:
        return await self._aget_text_embedding(query)

    def _get_text_embedding(self, text: str) -> Embedding:
        return self._get_text_embeddings([text])[0]

    async def _aget_text_embedding(self, text: str) -> Embedding:
        return (await self._aget_text_embeddings([text]))[0]

    def _get_text_embeddings(self, texts: list[str]) -> list[Embedding]:
        with httpx.Client(timeout=self.request_timeout) as client:
            response = client.post(
                f"{self.base_url}/v1/embeddings",
                json=self._embedding_payload(texts),
            )
            response.raise_for_status()
            return self._parse_embeddings(response.json())

    async def _aget_text_embeddings(self, texts: list[str]) -> list[Embedding]:
        async with httpx.AsyncClient(timeout=self.request_timeout) as client:
            response = await client.post(
                f"{self.base_url}/v1/embeddings",
                json=self._embedding_payload(texts),
            )
            response.raise_for_status()
            return self._parse_embeddings(response.json())


def get_embed_model() -> Any:
    if EMBEDDING_PROVIDER == "llama_cpp":
        try:
            from llama_index.embeddings.llama_cpp import LlamaCppEmbedding
        except ImportError as exc:
            msg = (
                "LLAMAINDEX_EMBEDDING_PROVIDER=llama_cpp requires the optional "
                "llama_index.embeddings.llama_cpp package, which is not "
                "available for every Python version. Use the default "
                "llamafile provider or install a compatible llama_cpp "
                "embedding integration."
            )
            raise RuntimeError(msg) from exc

        return LlamaCppEmbedding(
            base_url=EMBEDDINGS_BASE_URL,
            model_path=None,
        )

    if EMBEDDING_PROVIDER == "native_llamafile":
        from llama_index.embeddings.llamafile import LlamafileEmbedding

        return LlamafileEmbedding(base_url=EMBEDDINGS_BASE_URL)

    return LlamaCppServerEmbedding(
        base_url=EMBEDDINGS_BASE_URL,
        model=EMBEDDING_MODEL,
    )


def get_qdrant_client() -> QdrantClient:
    return QdrantClient(url=QDRANT_URL)


def get_vector_store(collection_name: str, client: QdrantClient | None = None):
    from llama_index.vector_stores.qdrant import QdrantVectorStore

    return QdrantVectorStore(
        client=client or get_qdrant_client(),
        collection_name=collection_name,
    )


def get_storage_context(collection_name: str, client: QdrantClient | None = None):
    from llama_index.core import StorageContext

    return StorageContext.from_defaults(vector_store=get_vector_store(collection_name, client))


def get_index(collection_name: str = DEFAULT_COLLECTION_NAME):
    from llama_index.core import VectorStoreIndex

    return VectorStoreIndex.from_vector_store(
        get_vector_store(collection_name),
        embed_model=get_embed_model(),
    )


def collection_exists(client: QdrantClient, collection_name: str) -> bool:
    try:
        return client.collection_exists(collection_name)
    except AttributeError:
        response = client.get_collections()
        return any(collection.name == collection_name for collection in response.collections)


def reset_collection(client: QdrantClient, collection_name: str) -> None:
    if collection_exists(client, collection_name):
        client.delete_collection(collection_name)


def delete_by_source(
    client: QdrantClient,
    collection_name: str,
    source: str,
) -> None:
    if not collection_exists(client, collection_name):
        return

    client.delete(
        collection_name=collection_name,
        points_selector=models.Filter(
            must=[
                models.FieldCondition(
                    key="source",
                    match=models.MatchValue(value=source),
                )
            ]
        ),
    )
