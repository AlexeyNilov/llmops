import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from llama_index.core.graph_stores.types import EntityNode, Relation

from llmops.api import main
from llmops.cli import cognitive_map, index_file
from llmops.infrastructure import embeddings, language_model, qdrant_store
from llmops.use_cases import answer_question
from llmops.use_cases import cognitive_map as cognitive_map_use_case
from llmops.use_cases import index_file as index_file_use_case


def test_embedding_adapter_orders_embeddings_by_response_index() -> None:
    embed_model = embeddings.LlamaCppServerEmbedding(
        base_url="http://embedding.test/",
        model="test",
    )

    parsed_embeddings = embed_model._parse_embeddings(
        {
            "data": [
                {"index": 1, "embedding": [0.2, 0.3]},
                {"index": 0, "embedding": [0.0, 0.1]},
            ]
        }
    )

    assert parsed_embeddings == [[0.0, 0.1], [0.2, 0.3]]
    assert embed_model.base_url == "http://embedding.test"


def test_delete_source_documents_deletes_only_matching_source_when_collection_exists(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = SimpleNamespace(delete_calls=[])

    def fake_delete(**kwargs: Any) -> None:
        client.delete_calls.append(kwargs)

    client.delete = fake_delete
    monkeypatch.setattr(qdrant_store, "collection_exists", lambda _client, _collection_name: True)

    qdrant_store.delete_source_documents(client, "knowledgebase", "guide.txt")

    assert len(client.delete_calls) == 1
    delete_call = client.delete_calls[0]
    assert delete_call["collection_name"] == "knowledgebase"
    condition = delete_call["points_selector"].must[0]
    assert condition.key == "source"
    assert condition.match.value == "guide.txt"


def test_get_async_vector_store_uses_async_qdrant_client(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}

    class FakeAsyncQdrantClient:
        def __init__(self, url: str) -> None:
            captured["client_url"] = url

    class FakeQdrantVectorStore:
        def __init__(self, **kwargs: Any) -> None:
            captured.update(kwargs)

    monkeypatch.setattr(qdrant_store, "QDRANT_URL", "http://qdrant.test")
    monkeypatch.setattr(qdrant_store, "AsyncQdrantClient", FakeAsyncQdrantClient)
    monkeypatch.setattr(qdrant_store, "QdrantVectorStore", FakeQdrantVectorStore)

    qdrant_store.get_async_vector_store("knowledgebase")

    assert captured["client_url"] == "http://qdrant.test"
    assert captured["collection_name"] == "knowledgebase"
    assert isinstance(captured["aclient"], FakeAsyncQdrantClient)
    assert "client" not in captured


def test_parse_llm_triplets_accepts_markdown_wrapped_triplets() -> None:
    output = """
    Based on the text:
    **(IA, is, cognitive infrastructure)**
    (IA artifact, improves, reasoning under constraints)
    not a triplet
    """

    triplets = cognitive_map_use_case.parse_llm_triplets(output)

    assert triplets == [
        ("IA", "is", "cognitive infrastructure"),
        ("IA artifact", "improves", "reasoning under constraints"),
    ]


def test_render_mermaid_concept_map_uses_graph_relations() -> None:
    graph = cognitive_map_use_case.SimplePropertyGraphStore()
    ia = EntityNode(name="IA", label="concept")
    reasoning = EntityNode(
        name="Reasoning under constraints",
        label="concept",
    )
    graph.upsert_nodes([ia, reasoning])
    graph.upsert_relations(
        [
            Relation(
                label="IMPROVES",
                source_id=ia.id,
                target_id=reasoning.id,
            )
        ]
    )

    rendered = cognitive_map_use_case.render_mermaid_concept_map(
        graph,
        title="IA cognitive map",
    )

    assert "# IA cognitive map" in rendered
    assert 'N0["IA"]' in rendered
    assert 'N1["Reasoning under constraints"]' in rendered
    assert 'N0 -- "IMPROVES" --> N1' in rendered


def test_load_markdown_document_rejects_blank_notes(tmp_path) -> None:
    filepath = tmp_path / "blank.md"
    filepath.write_text("\n\t", encoding="utf-8")

    with pytest.raises(ValueError, match="No content found"):
        cognitive_map_use_case.load_markdown_document(filepath)


@pytest.mark.asyncio
async def test_store_file_content_skips_blank_files_without_touching_vector_store(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    filepath = tmp_path / "blank.txt"
    filepath.write_text(" \n\t", encoding="utf-8")
    calls: list[str] = []

    monkeypatch.setattr(index_file_use_case, "get_qdrant_client", lambda: object())
    monkeypatch.setattr(
        index_file_use_case,
        "delete_source_documents",
        lambda *_args: calls.append("delete"),
    )
    monkeypatch.setattr(
        index_file_use_case,
        "reset_qdrant_collection",
        lambda *_args: calls.append("reset"),
    )
    monkeypatch.setattr(
        index_file_use_case,
        "VectorStoreIndex",
        lambda *_args, **_kwargs: calls.append("index"),
    )

    await index_file_use_case.FileIndexer().index_file(str(filepath))

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
async def test_index_file_uses_expected_retention_policy(
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

    monkeypatch.setattr(index_file_use_case, "SentenceSplitter", FakeSentenceSplitter)
    monkeypatch.setattr(index_file_use_case, "get_qdrant_client", lambda: object())
    monkeypatch.setattr(index_file_use_case, "get_storage_context", lambda *_args: object())
    monkeypatch.setattr(index_file_use_case, "get_embed_model", lambda: object())
    monkeypatch.setattr(index_file_use_case, "VectorStoreIndex", FakeVectorStoreIndex)
    monkeypatch.setattr(
        index_file_use_case,
        "delete_source_documents",
        lambda *_args: calls.append("delete"),
    )
    monkeypatch.setattr(
        index_file_use_case,
        "reset_qdrant_collection",
        lambda *_args: calls.append("reset"),
    )

    await index_file_use_case.FileIndexer().index_file(
        str(filepath),
        collection_name="knowledgebase",
        append=append,
        reset_collection=reset_collection,
    )

    assert calls == expected_calls


@pytest.mark.asyncio
async def test_get_rag_content_awaits_async_retrieval_and_joins_node_text(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}

    class FakeRetriever:
        def retrieve(self, _prompt: str) -> list[Any]:
            raise AssertionError("get_rag_content must not call sync retrieve")

        async def aretrieve(self, prompt: str) -> list[Any]:
            captured["prompt"] = prompt
            return [
                SimpleNamespace(node=SimpleNamespace(get_content=lambda: "first chunk")),
                SimpleNamespace(node=SimpleNamespace(get_content=lambda: "second chunk")),
            ]

    class FakeIndex:
        def as_retriever(self, similarity_top_k: int) -> FakeRetriever:
            captured["similarity_top_k"] = similarity_top_k
            return FakeRetriever()

    monkeypatch.setattr(answer_question, "get_async_index", lambda collection_name: FakeIndex())
    monkeypatch.setattr(answer_question, "RETRIEVAL_TOP_K", 2)

    content = await answer_question.get_rag_content("Where is the sentinel?")

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
    monkeypatch.setattr(language_model, "chat_client", fake_client)

    chunks = [chunk async for chunk in language_model.stream_text("Explain this")]

    assert chunks == ["hello", " world"]
    assert captured == {
        "model": language_model.CHAT_MODEL,
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
    log_messages: list[Any] = []

    async def fake_stream_text(prompt: str):
        captured_prompts.append(prompt)
        yield "answer"
        yield " text"

    monkeypatch.setattr(main, "stream_text", fake_stream_text)
    monkeypatch.setattr(main.logger, "info", lambda message: log_messages.append(message))

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
    assert "retrieved content" not in str(log_messages)
    assert "Answer this question" not in str(log_messages)


def test_embed_file_cli_rejects_append_and_reset_collection_together(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        ["embed_file.py", "guide.txt", "--append", "--reset-collection"],
    )

    with pytest.raises(SystemExit) as exc_info:
        index_file.parse_args()

    assert exc_info.value.code == 2


def test_cognitive_map_cli_defaults_to_markdown_output(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        ["cognitive_map.py", "input/note.md"],
    )

    args = cognitive_map.parse_args()

    assert args.filepath == "input/note.md"
    assert args.output_path == "doc/cognitive_maps/note.md"


def test_index_file_script_can_run_directly_without_pythonpath() -> None:
    script_path = Path("src/llmops/cli/index_file.py")

    result = subprocess.run(
        [sys.executable, str(script_path), "--help"],
        capture_output=True,
        check=False,
        text=True,
    )

    assert result.returncode == 0
    assert "Index a text file with LlamaIndex embeddings and Qdrant." in result.stdout
