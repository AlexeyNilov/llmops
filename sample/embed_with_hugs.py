from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_postgres.vectorstores import PGVector
from langchain_huggingface.embeddings import HuggingFaceEmbeddings
from conf.settings import VG_CONN
import time


def benchmark_model(documents: list, model_name: str):
    print(f"\n--- Benchmarking {model_name} ---")

    embeddings_model = HuggingFaceEmbeddings(model_name=model_name)

    # Embed + insert
    start = time.perf_counter()
    vector_store = PGVector.from_documents(
        documents, embeddings_model, connection=VG_CONN
    )
    embed_time = time.perf_counter() - start
    print(f"Embedding + insert time: {embed_time:.2f} sec")

    # Similarity search
    start = time.perf_counter()
    out = vector_store.similarity_search("What is peripheral vision?", k=1)
    search_time = time.perf_counter() - start
    print(f"Similarity search time: {search_time:.4f} sec")

    for item in out:
        print(item)

    # Cleanup
    vector_store.delete_collection()


models = [
    "sentence-transformers/all-MiniLM-L6-v2",
    "sentence-transformers/all-mpnet-base-v2",
    "answerdotai/ModernBERT-base",
]

# Load and split
raw_documents = TextLoader("db/in.txt").load()
text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
documents = text_splitter.split_documents(raw_documents)

for m in models:
    benchmark_model(documents, m)
