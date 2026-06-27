# LLMOPS

## Local RAG chat

The app uses LlamaIndex for embeddings and retrieval, with Qdrant as the vector
store. The main UI is a Streamlit chat client that calls the local FastAPI
server.

Install dependencies:

```bash
pip install -r requirements.txt
```

Start Qdrant on `http://localhost:6333`, then start a llama.cpp-compatible
embedding server. By default the app expects the embedding endpoint at
`http://127.0.0.1:12346`.

Useful environment variables:

```bash
export QDRANT_URL=http://localhost:6333
export QDRANT_COLLECTION_NAME=knowledgebase
export LLAMAINDEX_EMBEDDINGS_BASE_URL=http://127.0.0.1:12346
export LLAMAINDEX_EMBEDDING_PROVIDER=llamafile
export LLAMAINDEX_EMBEDDING_MODEL=v5-small-retrieval-Q8_0.gguf
export RAG_RETRIEVAL_TOP_K=2
export LLMOPS_GRAPH_CONTEXT_ENABLED=true
export LLMOPS_GRAPH_CONTEXT_TOP_K=15
export LLMOPS_GRAPH_LLM_MODEL=gemma-4-12b
export LLMOPS_GRAPH_PERSIST_DIR=.local/property_graph
export LLMOPS_GRAPH_CHUNK_SIZE=1200
export LLMOPS_GRAPH_CHUNK_OVERLAP=200
export LLMOPS_GRAPH_DISABLE_THINKING=true
```

The default `llamafile` provider uses this app's LlamaIndex-compatible adapter
for llama.cpp's OpenAI-style `/v1/embeddings` endpoint. Set
`LLAMAINDEX_EMBEDDING_PROVIDER=native_llamafile` only when running a server that
matches LlamaIndex's native `LlamafileEmbedding` `/embedding` response shape.

Index a file:

```bash
PYTHONPATH=src python -m llmops.cli.index_file path/to/file.txt --collection-name knowledgebase
```

Direct script execution is also supported:

```bash
python src/llmops/cli/index_file.py path/to/file.txt --collection-name knowledgebase
```

File processing uses LlamaIndex `Document` plus `SentenceSplitter` with the
splitter's default chunking settings.

By default, re-indexing a file replaces existing chunks for the same source
filename. Use `--append` to keep existing chunks, or `--reset-collection` to
delete and rebuild the whole collection.

Build a cognitive map from a Markdown note:

```bash
PYTHONPATH=src python -m llmops.cli.cognitive_map input/2026-05-04-ia-as-cognitive-infrastructure.md
```

The cognitive-map CLI uses LlamaIndex `PropertyGraphIndex` with a local
`SimplePropertyGraphStore`. It calls the LM Studio OpenAI-compatible chat
endpoint configured by `LM_STUDIO_CHAT_BASE_URL`, defaulting to
`http://127.0.0.1:12345/v1`, and uses `LLMOPS_GRAPH_LLM_MODEL`, defaulting to
`gemma-4-12b`. The command writes a Mermaid Markdown map to
`doc/cognitive_maps/<input-stem>.md` and persists the local graph under
`LLMOPS_GRAPH_PERSIST_DIR`.

Markdown inputs are split with LlamaIndex `MarkdownNodeParser` first, then split
into sentence chunks before graph extraction. For Gemma models served by
llama.cpp, `LLMOPS_GRAPH_DISABLE_THINKING=true` sends
`chat_template_kwargs.enable_thinking=false` so structured triples are returned
in `message.content` instead of the reasoning channel.

Select triples from the persisted graph for a question:

```bash
PYTHONPATH=src python -m llmops.cli.graph_context "How does IA support reasoning?"
```

The graph-context CLI loads `property_graph.json` from `LLMOPS_GRAPH_PERSIST_DIR`
and ranks triples by lexical overlap with the query. Use `--context` or
`--context-file` to include retrieved text when experimenting with hybrid RAG
and graph context.

Run the FastAPI app:

```bash
PYTHONPATH=src uvicorn llmops.api.main:app --reload
```

In another terminal, run the chat UI:

```bash
streamlit run src/llmops/ui/streamlit_chat.py
```

The Streamlit client sends prompts to `http://localhost:8000/generate/text` and
streams the response back into the chat.

The FastAPI request path uses async retrieval against Qdrant, then optionally
loads related triples from the persisted property graph before starting
chat-completion streaming. Source excerpts are the grounding evidence; graph
triples are prompt context for organizing relationships and distinctions. The
CLI indexing path keeps separate sync Qdrant helpers for collection maintenance
and batch indexing.

## App structure

The application code is organized by responsibility:

- `src/llmops/api`: FastAPI routing and HTTP middleware.
- `src/llmops/cli`: command-line entry points.
- `src/llmops/ui`: Streamlit UI entry points.
- `src/llmops/use_cases`: application workflows such as file indexing and RAG retrieval.
- `src/llmops/infrastructure`: adapters for Qdrant, embeddings, and chat-completion clients.
- `src/llmops/config.py`: environment-backed runtime settings.
