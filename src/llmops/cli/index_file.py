import argparse
import asyncio
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from llmops.config import DEFAULT_COLLECTION_NAME
from llmops.use_cases.index_file import file_indexer


async def index_file(
    filepath: str,
    collection_name: str,
    append: bool,
    reset_collection: bool,
) -> None:
    await file_indexer.index_file(
        filepath=filepath,
        collection_name=collection_name,
        append=append,
        reset_collection=reset_collection,
    )
    print(f"Stored embeddings for {filepath!r} in collection {collection_name!r}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Index a text file with LlamaIndex embeddings and Qdrant."
    )
    parser.add_argument("filepath")
    parser.add_argument("--collection-name", default=DEFAULT_COLLECTION_NAME)
    parser.add_argument(
        "--append",
        action="store_true",
        help="Append vectors instead of replacing existing chunks for this file.",
    )
    parser.add_argument(
        "--reset-collection",
        action="store_true",
        help="Delete and recreate the whole collection before inserting this file.",
    )
    args = parser.parse_args()
    if args.append and args.reset_collection:
        parser.error("--append and --reset-collection cannot be used together")
    return args


def main() -> None:
    args = parse_args()
    asyncio.run(
        index_file(
            args.filepath,
            args.collection_name,
            args.append,
            args.reset_collection,
        )
    )


if __name__ == "__main__":
    main()
