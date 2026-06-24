# rag/repository.py

from uuid import uuid4

from loguru import logger
from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import ScoredPoint


class VectorRepository:
    def __init__(self, host: str = "localhost", port: int = 6333) -> None:
        self.db_client = AsyncQdrantClient(host=host, port=port)

    async def create_collection(self, collection_name: str, size: int) -> bool:
        vectors_config = models.VectorParams(
            size=size, distance=models.Distance.COSINE
        )
        response = await self.db_client.get_collections()

        collection_exists = any(
            collection.name == collection_name
            for collection in response.collections
        )
        if collection_exists:
            collection = await self.db_client.get_collection(collection_name)
            current_size = collection.config.params.vectors.size
            if current_size != size:
                msg = (
                    f"Collection {collection_name} already exists with vector "
                    f"size {current_size}, but embedding model returned size "
                    f"{size}. Use --reset-collection to recreate it."
                )
                raise ValueError(msg)

            logger.debug(
                f"Collection {collection_name} already exists - reusing it"
            )
            return True

        logger.debug(f"Creating collection {collection_name}")
        return await self.db_client.create_collection(
            collection_name=collection_name,
            vectors_config=vectors_config,
        )

    async def recreate_collection(self, collection_name: str, size: int) -> bool:
        response = await self.db_client.get_collections()
        collection_exists = any(
            collection.name == collection_name
            for collection in response.collections
        )
        if collection_exists:
            logger.debug(f"Deleting existing collection {collection_name}")
            await self.db_client.delete_collection(collection_name)

        logger.debug(f"Recreating collection {collection_name}")
        return await self.db_client.create_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(
                size=size, distance=models.Distance.COSINE
            ),
        )

    async def delete_collection(self, name: str) -> bool:
        logger.debug(f"Deleting collection {name}")
        return await self.db_client.delete_collection(name)

    async def delete_by_source(
        self,
        collection_name: str,
        source: str,
    ) -> None:
        logger.debug(
            f"Deleting existing vectors from {collection_name} for source {source}"
        )
        await self.db_client.delete(
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

    async def create(
        self,
        collection_name: str,
        embedding_vector: list[float],
        original_text: str,
        source: str,
        chunk_index: int,
    ) -> None:
        point_id = str(uuid4())
        logger.debug(
            f"Creating a new vector with ID {point_id} inside {collection_name}"
        )
        await self.db_client.upsert(
            collection_name=collection_name,
            points=[
                models.PointStruct(
                    id=point_id,
                    vector=embedding_vector,
                    payload={
                        "source": source,
                        "chunk_index": chunk_index,
                        "original_text": original_text,
                    },
                )
            ],
        )

    async def search(
        self,
        collection_name: str,
        query_vector: list[float],
        retrieval_limit: int,
        score_threshold: float,
    ) -> list[ScoredPoint]:
        logger.debug(
            f"Searching for relevant items in the {collection_name} collection"
        )
        response = await self.db_client.query_points(
            collection_name=collection_name,
            query=query_vector,
            limit=retrieval_limit,
            score_threshold=score_threshold,
        )
        return response.points
