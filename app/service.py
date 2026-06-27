import os
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

from loguru import logger
from llama_index.core import Document, VectorStoreIndex
from llama_index.core.node_parser import SentenceSplitter

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
        collection_name: str = DEFAULT_COLLECTION_NAME,
        append: bool = False,
        reset_collection: bool = False,
    ) -> None:
        logger.debug(f"Inserting {filepath} content into database")
        client = get_qdrant_client()
        source = os.path.basename(filepath)
        text = Path(filepath).read_text(encoding="utf-8")

        if not text.strip():
            logger.warning(f"No content found in {filepath}; nothing inserted")
            return

        splitter = SentenceSplitter(
            id_func=lambda index, document: str(
                uuid5(NAMESPACE_URL, f"{document.metadata['source']}:{index}")
            ),
        )
        nodes = splitter.get_nodes_from_documents(
            [
                Document(
                    text=text,
                    metadata={"source": source},
                    id_=source,
                )
            ]
        )

        for chunk_index, node in enumerate(nodes):
            logger.debug(f"Inserting '{node.get_content()[0:20]}...' into database")
            node.metadata["chunk_index"] = chunk_index

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


async def get_rag_content(prompt: str) -> str:
    from index import get_index

    retriever = get_index(DEFAULT_COLLECTION_NAME).as_retriever(
        similarity_top_k=RETRIEVAL_TOP_K
    )
    rag_content = retriever.retrieve(prompt)
    rag_content_str = "\n".join(node.node.get_content() for node in rag_content)

    return rag_content_str
