import re
from collections.abc import Generator
from pathlib import Path
from typing import Any

from llama_index.core import Document
from llama_index.core.graph_stores.simple_labelled import SimplePropertyGraphStore
from llama_index.core.indices.property_graph import PropertyGraphIndex, SimpleLLMPathExtractor
from llama_index.core.llms import CompletionResponse, CustomLLM, LLMMetadata
from llama_index.core.node_parser import MarkdownNodeParser, SentenceSplitter
from llama_index.core.schema import TransformComponent
from loguru import logger
from openai import OpenAI

from llmops.config import (
    GRAPH_CHUNK_OVERLAP,
    GRAPH_CHUNK_SIZE,
    GRAPH_LLM_MODEL,
    GRAPH_MAX_PATHS_PER_CHUNK,
    GRAPH_PERSIST_DIR,
    LM_STUDIO_API_KEY,
    LM_STUDIO_CHAT_BASE_URL,
)

TRIPLET_PATTERN = re.compile(r"\(([^,\n]+),\s*([^,\n]+),\s*([^)]+)\)")
TRIPLET_EXTRACT_PROMPT = (
    "Extract concept triples from this text. Return only lines like "
    "(subject, relation, object).\n\nText:\n{text}"
)


class LMStudioLLM(CustomLLM):
    model: str
    api_base: str
    api_key: str
    temperature: float = 0.0
    max_tokens: int = 768
    timeout: float = 120
    context_window: int = 8192

    @property
    def metadata(self) -> LLMMetadata:
        return LLMMetadata(
            context_window=self.context_window,
            num_output=self.max_tokens,
            is_chat_model=True,
            model_name=self.model,
        )

    def complete(
        self,
        prompt: str,
        formatted: bool = False,
        **kwargs: Any,
    ) -> CompletionResponse:
        client = OpenAI(
            base_url=self.api_base,
            api_key=self.api_key,
            timeout=self.timeout,
        )
        response = client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
        content = response.choices[0].message.content or ""
        return CompletionResponse(text=content)

    def stream_complete(
        self,
        prompt: str,
        formatted: bool = False,
        **kwargs: Any,
    ) -> Generator[CompletionResponse, None, None]:
        yield self.complete(prompt, formatted=formatted, **kwargs)


def parse_llm_triplets(output: str) -> list[tuple[str, str, str]]:
    triplets: list[tuple[str, str, str]] = []
    for subject, predicate, object_ in TRIPLET_PATTERN.findall(output):
        triplets.append(
            (
                _clean_triplet_part(subject),
                _clean_triplet_part(predicate),
                _clean_triplet_part(object_),
            )
        )
    return [triplet for triplet in triplets if all(triplet)]


def load_markdown_document(filepath: Path) -> Document:
    text = filepath.read_text(encoding="utf-8")
    if not text.strip():
        raise ValueError(f"No content found in {filepath}")
    return Document(text=text, metadata={"source": filepath.name}, id_=filepath.name)


def build_cognitive_graph(
    filepath: Path,
    persist_dir: Path = Path(GRAPH_PERSIST_DIR),
    max_paths_per_chunk: int = GRAPH_MAX_PATHS_PER_CHUNK,
    chunk_size: int = GRAPH_CHUNK_SIZE,
    chunk_overlap: int = GRAPH_CHUNK_OVERLAP,
) -> SimplePropertyGraphStore:
    document = load_markdown_document(filepath)
    graph_store = SimplePropertyGraphStore()
    llm = _get_graph_llm()
    extractor = SimpleLLMPathExtractor(
        llm=llm,
        extract_prompt=TRIPLET_EXTRACT_PROMPT,
        parse_fn=parse_llm_triplets,
        max_paths_per_chunk=max_paths_per_chunk,
        num_workers=1,
    )
    logger.info({"event": "build_cognitive_graph", "source": str(filepath)})
    PropertyGraphIndex.from_documents(
        [document],
        llm=llm,
        kg_extractors=[extractor],
        property_graph_store=graph_store,
        transformations=build_graph_transformations(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        ),
        embed_kg_nodes=False,
        use_async=False,
        show_progress=True,
    )
    _persist_graph(graph_store, persist_dir)
    return graph_store


def render_mermaid_concept_map(
    graph_store: SimplePropertyGraphStore,
    title: str,
    max_relations: int = 80,
) -> str:
    graph = graph_store.to_dict()
    nodes = graph["nodes"]
    relations = list(graph["relations"].values())[:max_relations]
    node_ids = _node_ids_for_relations(relations)
    lines = [f"# {title}", "", "```mermaid", "flowchart TD"]
    lines.extend(_render_node_definitions(nodes, node_ids))
    lines.extend(_render_relation_lines(relations, node_ids))
    if not relations:
        lines.append('  empty["No graph relations were extracted"]')
    lines.extend(["```", "", "## Triples", ""])
    lines.extend(_render_triples(relations))
    return "\n".join(lines)


def write_cognitive_map(
    filepath: Path,
    output_path: Path,
    persist_dir: Path = Path(GRAPH_PERSIST_DIR),
) -> Path:
    graph_store = build_cognitive_graph(filepath, persist_dir)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        render_mermaid_concept_map(graph_store, title=filepath.stem),
        encoding="utf-8",
    )
    return output_path


def build_graph_transformations(
    chunk_size: int = GRAPH_CHUNK_SIZE,
    chunk_overlap: int = GRAPH_CHUNK_OVERLAP,
) -> list[TransformComponent]:
    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be smaller than chunk_size")
    return [
        MarkdownNodeParser.from_defaults(),
        SentenceSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap),
    ]


def _get_graph_llm() -> LMStudioLLM:
    return LMStudioLLM(
        model=GRAPH_LLM_MODEL,
        api_base=LM_STUDIO_CHAT_BASE_URL,
        api_key=LM_STUDIO_API_KEY,
        temperature=0.0,
        max_tokens=768,
        timeout=120,
    )


def _persist_graph(graph_store: SimplePropertyGraphStore, persist_dir: Path) -> None:
    persist_dir.mkdir(parents=True, exist_ok=True)
    graph_store.persist(str(persist_dir / "property_graph.json"))


def _clean_triplet_part(value: str) -> str:
    return value.strip().strip("*`_ ").replace("\n", " ")


def _node_ids_for_relations(relations: list[dict[str, object]]) -> dict[str, str]:
    node_ids: dict[str, str] = {}
    for relation in relations:
        for key in ("source_id", "target_id"):
            node_id = str(relation[key])
            if node_id not in node_ids:
                node_ids[node_id] = f"N{len(node_ids)}"
    return node_ids


def _render_node_definitions(nodes: dict[str, object], node_ids: dict[str, str]) -> list[str]:
    lines: list[str] = []
    for node_id, mermaid_id in node_ids.items():
        node = nodes.get(node_id, {})
        label = _node_label(node_id, node)
        lines.append(f'  {mermaid_id}["{_escape_mermaid(label)}"]')
    return lines


def _render_relation_lines(
    relations: list[dict[str, object]],
    node_ids: dict[str, str],
) -> list[str]:
    lines: list[str] = []
    for relation in relations:
        source = node_ids[str(relation["source_id"])]
        target = node_ids[str(relation["target_id"])]
        label = _escape_mermaid(str(relation["label"]))
        lines.append(f'  {source} -- "{label}" --> {target}')
    return lines


def _render_triples(relations: list[dict[str, object]]) -> list[str]:
    if not relations:
        return ["No graph relations were extracted."]
    lines = ["| Subject | Relation | Object |", "| --- | --- | --- |"]
    for relation in relations:
        lines.append(f"| {relation['source_id']} | {relation['label']} | {relation['target_id']} |")
    return lines


def _node_label(node_id: str, node: object) -> str:
    if isinstance(node, dict):
        return str(node.get("name") or node.get("text") or node_id)
    return node_id


def _escape_mermaid(value: str) -> str:
    return value.replace('"', "'").replace("\n", " ")
