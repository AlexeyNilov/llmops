import asyncio
from dataclasses import dataclass
from pathlib import Path

from llmops.config import (
    DEFAULT_COLLECTION_NAME,
    GRAPH_CONTEXT_ENABLED,
    GRAPH_CONTEXT_TOP_K,
    GRAPH_PERSIST_DIR,
    RETRIEVAL_TOP_K,
)
from llmops.infrastructure.qdrant_store import get_async_index
from llmops.use_cases.graph_context import (
    format_graph_triples,
    load_graph_triples,
    select_related_triples,
)


@dataclass(frozen=True)
class AnswerContext:
    rag_content: str
    graph_content: str


def build_answer_prompt(question: str, context: AnswerContext) -> str:
    sections = [
        "Answer the user's question using the source excerpts as the grounding evidence.",
        "Use concept relations to organize the answer, expose relationships, and suggest "
        "useful distinctions.",
        "Do not treat concept relations as standalone proof when unsupported by the source "
        "excerpts.",
        "If the source excerpts do not support an answer, say what is missing.",
        "",
        "Question:",
        question,
        "",
        "Source excerpts:",
        context.rag_content,
    ]
    if context.graph_content:
        sections.extend(["", "Concept relations:", context.graph_content])
    return "\n".join(sections)


async def get_rag_content(prompt: str) -> str:
    retriever = get_async_index(DEFAULT_COLLECTION_NAME).as_retriever(
        similarity_top_k=RETRIEVAL_TOP_K
    )
    rag_content = await retriever.aretrieve(prompt)
    return "\n".join(node.node.get_content() for node in rag_content)


async def get_answer_context(prompt: str) -> AnswerContext:
    rag_content = await get_rag_content(prompt)
    graph_content = await asyncio.to_thread(get_graph_content, prompt, rag_content)
    return AnswerContext(rag_content=rag_content, graph_content=graph_content)


def get_graph_content(prompt: str, rag_content: str) -> str:
    if not GRAPH_CONTEXT_ENABLED:
        return ""
    try:
        triples = load_graph_triples(Path(GRAPH_PERSIST_DIR))
    except (OSError, ValueError):
        return ""
    related_triples = select_related_triples(
        triples,
        query=prompt,
        context=rag_content,
        limit=GRAPH_CONTEXT_TOP_K,
    )
    return format_graph_triples(related_triples)
