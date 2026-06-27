from typing import Any

from llama_index.vector_stores.qdrant import QdrantVectorStore
from qdrant_client import AsyncQdrantClient, QdrantClient
from qdrant_client.http import models as qdrant_models

from llmops.config import DEFAULT_COLLECTION_NAME, QDRANT_URL
from llmops.infrastructure.embeddings import get_embed_model


def get_qdrant_client() -> QdrantClient:
    return QdrantClient(url=QDRANT_URL)


def get_async_qdrant_client() -> AsyncQdrantClient:
    return AsyncQdrantClient(url=QDRANT_URL)


def get_vector_store(collection_name: str, client: QdrantClient | None = None) -> Any:
    return QdrantVectorStore(
        client=client or get_qdrant_client(),
        collection_name=collection_name,
    )


def get_async_vector_store(
    collection_name: str,
    client: AsyncQdrantClient | None = None,
) -> Any:
    return QdrantVectorStore(
        aclient=client or get_async_qdrant_client(),
        collection_name=collection_name,
    )


def get_storage_context(collection_name: str, client: QdrantClient | None = None) -> Any:
    from llama_index.core import StorageContext

    return StorageContext.from_defaults(vector_store=get_vector_store(collection_name, client))


def get_index(collection_name: str = DEFAULT_COLLECTION_NAME) -> Any:
    from llama_index.core import VectorStoreIndex

    return VectorStoreIndex.from_vector_store(
        get_vector_store(collection_name),
        embed_model=get_embed_model(),
    )


def get_async_index(collection_name: str = DEFAULT_COLLECTION_NAME) -> Any:
    from llama_index.core import VectorStoreIndex

    return VectorStoreIndex.from_vector_store(
        get_async_vector_store(collection_name),
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


def delete_source_documents(
    client: QdrantClient,
    collection_name: str,
    source: str,
) -> None:
    if not collection_exists(client, collection_name):
        return

    client.delete(
        collection_name=collection_name,
        points_selector=qdrant_models.Filter(
            must=[
                qdrant_models.FieldCondition(
                    key="source",
                    match=qdrant_models.MatchValue(value=source),
                )
            ]
        ),
    )
