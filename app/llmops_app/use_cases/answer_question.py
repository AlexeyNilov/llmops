from llmops_app.config import DEFAULT_COLLECTION_NAME, RETRIEVAL_TOP_K
from llmops_app.infrastructure.qdrant_store import get_index


def build_answer_prompt(question: str, rag_content: str) -> str:
    return f"Answer this question: '{question}' based on this content: {rag_content}"


async def get_rag_content(prompt: str) -> str:
    retriever = get_index(DEFAULT_COLLECTION_NAME).as_retriever(similarity_top_k=RETRIEVAL_TOP_K)
    rag_content = retriever.retrieve(prompt)
    return "\n".join(node.node.get_content() for node in rag_content)
