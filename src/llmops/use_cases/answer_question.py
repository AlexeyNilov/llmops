from llmops.config import DEFAULT_COLLECTION_NAME, RETRIEVAL_TOP_K
from llmops.infrastructure.qdrant_store import get_async_index


def build_answer_prompt(question: str, rag_content: str) -> str:
    return f"Answer this question: '{question}' based on this content: {rag_content}"


async def get_rag_content(prompt: str) -> str:
    retriever = get_async_index(DEFAULT_COLLECTION_NAME).as_retriever(
        similarity_top_k=RETRIEVAL_TOP_K
    )
    rag_content = await retriever.aretrieve(prompt)
    return "\n".join(node.node.get_content() for node in rag_content)
