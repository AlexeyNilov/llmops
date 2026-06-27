import os
from uuid import NAMESPACE_URL, uuid5

from loguru import logger
from llama_index.core import VectorStoreIndex
from llama_index.core.schema import TextNode

from embeddings import clean, load
from index import (
    DEFAULT_COLLECTION_NAME,
    RETRIEVAL_TOP_K,
    delete_by_source,
    get_embed_model,
    get_qdrant_client,
    get_storage_context,
    reset_collection as reset_qdrant_collection,
)


class VectorService:
    async def store_file_content_in_db(
        self,
        filepath: str,
        chunk_size: int = 512,
        collection_name: str = DEFAULT_COLLECTION_NAME,
        collection_size: int | None = None,
        append: bool = False,
        reset_collection: bool = False,
    ) -> None:
        if collection_size is not None:
            logger.warning(
                f"Ignoring collection_size={collection_size}; "
                "LlamaIndex/Qdrant infer vector size from the embedding model"
            )

        logger.debug(f"Inserting {filepath} content into database")
        client = get_qdrant_client()
        source = os.path.basename(filepath)
        nodes: list[TextNode] = []

        async for chunk_index, chunk in async_enumerate(load(filepath, chunk_size)):
            logger.debug(f"Inserting '{chunk[0:20]}...' into database")
            nodes.append(
                TextNode(
                    text=clean(chunk),
                    id_=str(uuid5(NAMESPACE_URL, f"{source}:{chunk_index}")),
                    metadata={
                        "source": source,
                        "chunk_index": chunk_index,
                        "original_text": chunk,
                    },
                )
            )

        if not nodes:
            logger.warning(f"No content found in {filepath}; nothing inserted")
            return

        if reset_collection:
            reset_qdrant_collection(client, collection_name)
        elif not append:
            delete_by_source(client, collection_name, source)

        VectorStoreIndex(
            nodes,
            storage_context=get_storage_context(collection_name, client),
            embed_model=get_embed_model(),
        )


vector_service = VectorService()


async def async_enumerate(async_iterable, start: int = 0):
    index = start
    async for item in async_iterable:
        yield index, item
        index += 1


async def get_rag_content(prompt: str) -> str:
    from index import get_index

    retriever = get_index(DEFAULT_COLLECTION_NAME).as_retriever(
        similarity_top_k=RETRIEVAL_TOP_K
    )
    rag_content = retriever.retrieve(prompt)
    rag_content_str = "\n".join(
        node.node.get_content() for node in rag_content
    )

    return rag_content_str
