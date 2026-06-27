import os
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

from llama_index.core import Document, VectorStoreIndex
from llama_index.core.node_parser import SentenceSplitter
from loguru import logger

from llmops_app.config import DEFAULT_COLLECTION_NAME
from llmops_app.infrastructure.embeddings import get_embed_model
from llmops_app.infrastructure.qdrant_store import (
    delete_source_documents,
    get_qdrant_client,
    get_storage_context,
)
from llmops_app.infrastructure.qdrant_store import (
    reset_collection as reset_qdrant_collection,
)


class FileIndexer:
    async def index_file(
        self,
        filepath: str,
        collection_name: str = DEFAULT_COLLECTION_NAME,
        append: bool = False,
        reset_collection: bool = False,
    ) -> None:
        logger.debug(f"Inserting {filepath} content into database")
        source = os.path.basename(filepath)
        text = Path(filepath).read_text(encoding="utf-8")

        if not text.strip():
            logger.warning(f"No content found in {filepath}; nothing inserted")
            return

        nodes = _split_file_content(source, text)
        if not nodes:
            logger.warning(f"No content found in {filepath}; nothing inserted")
            return

        client = get_qdrant_client()
        if reset_collection:
            reset_qdrant_collection(client, collection_name)
        elif not append:
            delete_source_documents(client, collection_name, source)

        VectorStoreIndex(
            nodes,
            storage_context=get_storage_context(collection_name, client),
            embed_model=get_embed_model(),
        )


def _split_file_content(source: str, text: str):
    splitter = SentenceSplitter(
        id_func=lambda index, document: str(
            uuid5(NAMESPACE_URL, f"{document.metadata['source']}:{index}")
        ),
    )
    nodes = splitter.get_nodes_from_documents(
        [Document(text=text, metadata={"source": source}, id_=source)]
    )

    for chunk_index, node in enumerate(nodes):
        logger.debug(f"Inserting '{node.get_content()[0:20]}...' into database")
        node.metadata["chunk_index"] = chunk_index

    return nodes


file_indexer = FileIndexer()
