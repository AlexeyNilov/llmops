import json
import re
from pathlib import Path
from typing import TypeAlias

Triple: TypeAlias = tuple[str, str, str]

GRAPH_FILENAME = "property_graph.json"
TOKEN_PATTERN = re.compile(r"[a-z0-9]+")
STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "for",
    "how",
    "in",
    "is",
    "it",
    "of",
    "or",
    "the",
    "to",
    "what",
    "with",
}


def load_graph_triples(persist_dir: Path) -> list[Triple]:
    graph_path = persist_dir / GRAPH_FILENAME
    data = json.loads(graph_path.read_text(encoding="utf-8"))
    return [_parse_triple(triple) for triple in data.get("triplets", [])]


def select_related_triples(
    triples: list[Triple],
    query: str,
    context: str = "",
    limit: int = 15,
) -> list[Triple]:
    search_tokens = _tokens(f"{query} {context}")
    scored = [
        (_overlap_score(triple, search_tokens), index, triple)
        for index, triple in enumerate(triples)
    ]
    ranked = sorted(scored, key=lambda item: (-item[0], item[1]))
    return [triple for score, _index, triple in ranked[:limit] if score > 0]


def format_graph_triples(triples: list[Triple]) -> str:
    return "\n".join(
        f"- {subject} -- {predicate} --> {object_}" for subject, predicate, object_ in triples
    )


def _parse_triple(value: object) -> Triple:
    if not isinstance(value, list | tuple) or len(value) != 3:
        raise ValueError(f"Invalid graph triple: {value!r}")
    subject, predicate, object_ = value
    return str(subject), str(predicate), str(object_)


def _overlap_score(triple: Triple, search_tokens: set[str]) -> int:
    triple_tokens = _tokens(" ".join(triple))
    return len(triple_tokens & search_tokens)


def _tokens(value: str) -> set[str]:
    return {token for token in TOKEN_PATTERN.findall(value.lower()) if token not in STOPWORDS}
