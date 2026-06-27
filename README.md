# LLMOPS

## Local RAG indexing

The app uses LlamaIndex for embeddings and retrieval, with Qdrant as the vector
store.

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
python app/embed_file.py path/to/file.txt --collection-name knowledgebase
```

By default, re-indexing a file replaces existing chunks for the same source
filename. Use `--append` to keep existing chunks, or `--reset-collection` to
delete and rebuild the whole collection.

Run the FastAPI app:

```bash
PYTHONPATH=app uvicorn main:app --reload
```
