from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_postgres.vectorstores import PGVector

# from langchain_core.documents import Document
from langchain_huggingface.embeddings import HuggingFaceEmbeddings

# import uuid
from conf.settings import VG_CONN

embeddings_model = HuggingFaceEmbeddings(model_name="answerdotai/ModernBERT-base")

# Load the document, split it into chunks
raw_documents = TextLoader("db/in.txt").load()
text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
documents = text_splitter.split_documents(raw_documents)

# Embed each chunk and insert it into the vector store
vector_store = PGVector.from_documents(documents, embeddings_model, connection=VG_CONN)

out = vector_store.similarity_search("What is peripheral vision?", k=1)
for item in out:
    print(item)

vector_store.delete_collection()
