# rag/service.py

import os

from loguru import logger
from repository import VectorRepository
from embeddings import clean, embed, load


class VectorService(VectorRepository):
    def __init__(self):
        super().__init__()

    async def store_file_content_in_db(
        self,
        filepath: str,
        chunk_size: int = 512,
        collection_name: str = "knowledgebase",
        collection_size: int | None = None,
        append: bool = False,
        reset_collection: bool = False,
    ) -> None:
        logger.debug(f"Inserting {filepath} content into database")
        collection_created = False
        source = os.path.basename(filepath)

        async for chunk_index, chunk in async_enumerate(load(filepath, chunk_size)):
            logger.debug(f"Inserting '{chunk[0:20]}...' into database")

            embedding_vector = await embed(clean(chunk))
            if not collection_created:
                vector_size = collection_size or len(embedding_vector)
                if reset_collection:
                    await self.recreate_collection(collection_name, vector_size)
                else:
                    await self.create_collection(collection_name, vector_size)
                    if not append:
                        await self.delete_by_source(collection_name, source)
                collection_created = True

            await self.create(
                collection_name,
                embedding_vector,
                chunk,
                source,
                chunk_index,
            )

        if not collection_created:
            logger.warning(f"No content found in {filepath}; nothing inserted")


vector_service = VectorService()


async def async_enumerate(async_iterable, start: int = 0):
    index = start
    async for item in async_iterable:
        yield index, item
        index += 1


async def get_rag_content(prompt: str) -> str:
    rag_content = await vector_service.search(
        "knowledgebase", await embed(prompt), 2, 0.4
    )
    rag_content_str = "\n".join([c.payload["original_text"] for c in rag_content])

    return rag_content_str
