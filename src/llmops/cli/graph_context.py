import argparse
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from llmops.config import GRAPH_PERSIST_DIR
from llmops.use_cases.graph_context import (
    format_graph_triples,
    load_graph_triples,
    select_related_triples,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Select graph triples related to a query.")
    parser.add_argument("query")
    parser.add_argument(
        "--context",
        default="",
        help="Optional extra text to use when matching graph triples.",
    )
    parser.add_argument(
        "--context-file",
        help="Optional file whose text should be used when matching graph triples.",
    )
    parser.add_argument(
        "--persist-dir",
        default=GRAPH_PERSIST_DIR,
        help="Directory containing property_graph.json.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=15,
        help="Maximum number of related triples to print.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    triples = load_graph_triples(Path(args.persist_dir))
    context = _read_context(args.context, args.context_file)
    related_triples = select_related_triples(
        triples,
        query=args.query,
        context=context,
        limit=args.limit,
    )
    output = format_graph_triples(related_triples)
    print(output or "No related graph triples found.")


def _read_context(context: str, context_file: str | None) -> str:
    if context_file is None:
        return context
    file_context = Path(context_file).read_text(encoding="utf-8")
    return f"{context}\n{file_context}".strip()


if __name__ == "__main__":
    main()
