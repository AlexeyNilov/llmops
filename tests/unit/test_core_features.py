import sys
from types import SimpleNamespace
from typing import Any

import embed_file
import index
import main
import models
import pytest
import service


def test_embedding_adapter_orders_embeddings_by_response_index() -> None:
    embed_model = index.LlamaCppServerEmbedding(base_url="http://embedding.test/", model="test")

    embeddings = embed_model._parse_embeddings(
        {
            "data": [
                {"index": 1, "embedding": [0.2, 0.3]},
                {"index": 0, "embedding": [0.0, 0.1]},
            ]
        }
    )

    assert embeddings == [[0.0, 0.1], [0.2, 0.3]]
    assert embed_model.base_url == "http://embedding.test"


def test_delete_by_source_deletes_only_matching_source_when_collection_exists(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = SimpleNamespace(delete_calls=[])

    def fake_delete(**kwargs: Any) -> None:
        client.delete_calls.append(kwargs)

    client.delete = fake_delete
    monkeypatch.setattr(index, "collection_exists", lambda _client, _collection_name: True)

    index.delete_by_source(client, "knowledgebase", "guide.txt")

    assert len(client.delete_calls) == 1
    delete_call = client.delete_calls[0]
    assert delete_call["collection_name"] == "knowledgebase"
    condition = delete_call["points_selector"].must[0]
    assert condition.key == "source"
    assert condition.match.value == "guide.txt"


@pytest.mark.asyncio
async def test_store_file_content_skips_blank_files_without_touching_vector_store(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    filepath = tmp_path / "blank.txt"
    filepath.write_text(" \n\t", encoding="utf-8")
    calls: list[str] = []

    monkeypatch.setattr(service, "get_qdrant_client", lambda: object())
    monkeypatch.setattr(service, "delete_by_source", lambda *_args: calls.append("delete"))
    monkeypatch.setattr(service, "reset_qdrant_collection", lambda *_args: calls.append("reset"))
    monkeypatch.setattr(
        service,
        "VectorStoreIndex",
        lambda *_args, **_kwargs: calls.append("index"),
    )

    await service.VectorService().store_file_content_in_db(str(filepath))

    assert calls == []


@pytest.mark.parametrize(
    ("append", "reset_collection", "expected_calls"),
    [
        (False, False, ["delete", "index"]),
        (True, False, ["index"]),
        (False, True, ["reset", "index"]),
    ],
)
@pytest.mark.asyncio
async def test_store_file_content_uses_expected_retention_policy(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
    append: bool,
    reset_collection: bool,
    expected_calls: list[str],
) -> None:
    filepath = tmp_path / "guide.txt"
    filepath.write_text("The e2e sentinel is stored in this document.", encoding="utf-8")
    calls: list[str] = []

    class FakeNode:
        def __init__(self) -> None:
            self.metadata: dict[str, Any] = {}

        def get_content(self) -> str:
            return "The e2e sentinel is stored in this document."

    class FakeSentenceSplitter:
        def __init__(self, **_kwargs: Any) -> None:
            pass

        def get_nodes_from_documents(self, _documents: list[Any]) -> list[FakeNode]:
            return [FakeNode()]

    class FakeVectorStoreIndex:
        def __init__(self, nodes: list[FakeNode], **_kwargs: Any) -> None:
            calls.append("index")
            assert nodes[0].metadata["chunk_index"] == 0

    monkeypatch.setattr(service, "SentenceSplitter", FakeSentenceSplitter)
    monkeypatch.setattr(service, "get_qdrant_client", lambda: object())
    monkeypatch.setattr(service, "get_storage_context", lambda *_args: object())
    monkeypatch.setattr(service, "get_embed_model", lambda: object())
    monkeypatch.setattr(service, "VectorStoreIndex", FakeVectorStoreIndex)
    monkeypatch.setattr(service, "delete_by_source", lambda *_args: calls.append("delete"))
    monkeypatch.setattr(service, "reset_qdrant_collection", lambda *_args: calls.append("reset"))

    await service.VectorService().store_file_content_in_db(
        str(filepath),
        collection_name="knowledgebase",
        append=append,
        reset_collection=reset_collection,
    )

    assert calls == expected_calls


@pytest.mark.asyncio
async def test_get_rag_content_joins_retrieved_node_text_with_configured_top_k(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}

    class FakeRetriever:
        def retrieve(self, prompt: str) -> list[Any]:
            captured["prompt"] = prompt
            return [
                SimpleNamespace(node=SimpleNamespace(get_content=lambda: "first chunk")),
                SimpleNamespace(node=SimpleNamespace(get_content=lambda: "second chunk")),
            ]

    class FakeIndex:
        def as_retriever(self, similarity_top_k: int) -> FakeRetriever:
            captured["similarity_top_k"] = similarity_top_k
            return FakeRetriever()

    monkeypatch.setattr(index, "get_index", lambda collection_name: FakeIndex())
    monkeypatch.setattr(service, "RETRIEVAL_TOP_K", 2)

    content = await service.get_rag_content("Where is the sentinel?")

    assert content == "first chunk\nsecond chunk"
    assert captured == {"similarity_top_k": 2, "prompt": "Where is the sentinel?"}


@pytest.mark.asyncio
async def test_stream_text_sends_chat_prompt_and_yields_only_non_empty_chunks(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}

    async def fake_stream():
        yield SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content="hello"))])
        yield SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content=None))])
        yield SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content=" world"))])

    class FakeCompletions:
        async def create(self, **kwargs: Any) -> Any:
            captured.update(kwargs)
            return fake_stream()

    fake_client = SimpleNamespace(chat=SimpleNamespace(completions=FakeCompletions()))
    monkeypatch.setattr(models, "chat_client", fake_client)

    chunks = [chunk async for chunk in models.stream_text("Explain this")]

    assert chunks == ["hello", " world"]
    assert captured == {
        "model": models.CHAT_MODEL,
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Explain this"},
        ],
        "stream": True,
    }


@pytest.mark.asyncio
async def test_generate_text_controller_combines_prompt_with_rag_content_and_streams_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured_prompts: list[str] = []

    async def fake_stream_text(prompt: str):
        captured_prompts.append(prompt)
        yield "answer"
        yield " text"

    monkeypatch.setattr(main, "stream_text", fake_stream_text)

    response = await main.serve_language_model_controller(
        prompt="What is stored?",
        rag_content="retrieved content",
    )
    chunks = [chunk async for chunk in response.body_iterator]

    assert chunks == ["answer", " text"]
    assert response.media_type == "text/plain"
    assert captured_prompts == [
        "Answer this question: 'What is stored?' based on this content: retrieved content"
    ]


def test_embed_file_cli_rejects_append_and_reset_collection_together(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        ["embed_file.py", "guide.txt", "--append", "--reset-collection"],
    )

    with pytest.raises(SystemExit) as exc_info:
        embed_file.parse_args()

    assert exc_info.value.code == 2
