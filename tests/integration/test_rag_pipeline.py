import os

import pytest

from llmops.config import DEFAULT_COLLECTION_NAME
from llmops.use_cases.answer_question import get_rag_content
from llmops.use_cases.index_file import FileIndexer

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_index_then_retrieve_returns_content_from_uploaded_file(tmp_path) -> None:
    if os.getenv("LLMOPS_RUN_INTEGRATION") != "1":
        pytest.skip("Set LLMOPS_RUN_INTEGRATION=1 when Qdrant and embeddings are running.")

    filepath = tmp_path / "sentinel.txt"
    filepath.write_text(
        "The integration sentinel answer is qdrant-llamafile-ready.",
        encoding="utf-8",
    )

    await FileIndexer().index_file(
        str(filepath),
        collection_name=DEFAULT_COLLECTION_NAME,
        reset_collection=True,
    )

    content = await get_rag_content("What is the integration sentinel answer?")

    assert "qdrant-llamafile-ready" in content
