import os
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.http import models

DEFAULT_QDRANT_URL = "http://localhost:6333"
DEFAULT_EMBEDDINGS_BASE_URL = "http://127.0.0.1:12346"

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
RETRIEVAL_TOP_K = int(os.getenv("RAG_RETRIEVAL_TOP_K", "2"))


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

    from llama_index.embeddings.llamafile import LlamafileEmbedding

    return LlamafileEmbedding(base_url=EMBEDDINGS_BASE_URL)


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

    return StorageContext.from_defaults(
        vector_store=get_vector_store(collection_name, client)
    )


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
        return any(
            collection.name == collection_name
            for collection in response.collections
        )


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
