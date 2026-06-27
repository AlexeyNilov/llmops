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
```

The default `llamafile` provider uses this app's LlamaIndex-compatible adapter
for llama.cpp's OpenAI-style `/v1/embeddings` endpoint. Set
`LLAMAINDEX_EMBEDDING_PROVIDER=native_llamafile` only when running a server that
matches LlamaIndex's native `LlamafileEmbedding` `/embedding` response shape.

Index a file:

```bash
PYTHONPATH=app python -m llmops_app.cli.index_file path/to/file.txt --collection-name knowledgebase
```

Direct script execution is also supported:

```bash
python app/llmops_app/cli/index_file.py path/to/file.txt --collection-name knowledgebase
```

File processing uses LlamaIndex `Document` plus `SentenceSplitter` with the
splitter's default chunking settings.

By default, re-indexing a file replaces existing chunks for the same source
filename. Use `--append` to keep existing chunks, or `--reset-collection` to
delete and rebuild the whole collection.

Run the FastAPI app:

```bash
PYTHONPATH=app uvicorn llmops_app.api.main:app --reload
```

In another terminal, run the chat UI:

```bash
streamlit run app/llmops_app/ui/streamlit_chat.py
```

The Streamlit client sends prompts to `http://localhost:8000/generate/text` and
streams the response back into the chat.

## App structure

The application code is organized by responsibility:

- `llmops_app/api`: FastAPI routing and HTTP middleware.
- `llmops_app/cli`: command-line entry points.
- `llmops_app/ui`: Streamlit UI entry points.
- `llmops_app/use_cases`: application workflows such as file indexing and RAG retrieval.
- `llmops_app/infrastructure`: adapters for Qdrant, embeddings, and chat-completion clients.
- `llmops_app/config.py`: environment-backed runtime settings.
