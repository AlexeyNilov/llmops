import argparse
import asyncio

from service import vector_service


async def embed_file(
    filepath: str,
    collection_name: str,
    collection_size: int | None,
    append: bool,
    reset_collection: bool,
) -> None:
    await vector_service.store_file_content_in_db(
        filepath=filepath,
        collection_name=collection_name,
        collection_size=collection_size,
        append=append,
        reset_collection=reset_collection,
    )
    print(
        f"Stored embeddings for {filepath!r} in collection "
        f"{collection_name!r}"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Index a text file with LlamaIndex embeddings and Qdrant."
    )
    parser.add_argument("filepath")
    parser.add_argument("--collection-name", default="knowledgebase")
    parser.add_argument(
        "--collection-size",
        type=int,
        default=None,
        help=(
            "Deprecated. LlamaIndex/Qdrant infer vector size from the "
            "embedding model."
        ),
    )
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


if __name__ == "__main__":
    args = parse_args()
    asyncio.run(
        embed_file(
            args.filepath,
            args.collection_name,
            args.collection_size,
            args.append,
            args.reset_collection,
        )
    )
