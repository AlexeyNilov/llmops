import argparse
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from llmops.use_cases.cognitive_map import write_cognitive_map


def default_output_path(filepath: str) -> str:
    return str(Path("doc/cognitive_maps") / f"{Path(filepath).stem}.md")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a LlamaIndex property graph and Mermaid cognitive map."
    )
    parser.add_argument("filepath")
    parser.add_argument("--output-path")
    parser.add_argument(
        "--persist-dir",
        default=".local/property_graph",
        help="Directory for the serialized simple property graph.",
    )
    args = parser.parse_args()
    args.output_path = args.output_path or default_output_path(args.filepath)
    return args


def main() -> None:
    args = parse_args()
    output_path = write_cognitive_map(
        filepath=Path(args.filepath),
        output_path=Path(args.output_path),
        persist_dir=Path(args.persist_dir),
    )
    print(f"Wrote cognitive map to {output_path}")


if __name__ == "__main__":
    main()
