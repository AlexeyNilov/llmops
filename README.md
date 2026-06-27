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
`http://127.0.0.1:12345`.

Useful environment variables:

```bash
export QDRANT_URL=http://localhost:6333
export QDRANT_COLLECTION_NAME=knowledgebase
export LLAMAINDEX_EMBEDDINGS_BASE_URL=http://127.0.0.1:12345
export LLAMAINDEX_EMBEDDING_PROVIDER=llamafile
export RAG_RETRIEVAL_TOP_K=2
```

The default provider is `LlamafileEmbedding`, which works with a
llama.cpp-style local embedding server. `LLAMAINDEX_EMBEDDING_PROVIDER=llama_cpp`
is also recognized by the code, but that optional LlamaIndex integration is not
available for every Python version.

Index a file:

```bash
python app/embed_file.py path/to/file.txt --collection-name knowledgebase
```

By default, re-indexing a file replaces existing chunks for the same source
filename. Use `--append` to keep existing chunks, or `--reset-collection` to
delete and rebuild the whole collection.

Run the FastAPI app:

```bash
uvicorn app.main:app --reload
```
