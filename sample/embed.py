from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_postgres.vectorstores import PGVector

# from langchain_core.documents import Document
from langchain_community.embeddings import HuggingFaceEmbeddings

# import uuid
from conf.settings import VG_CONN

embeddings_model = HuggingFaceEmbeddings(model_name="answerdotai/ModernBERT-base")

# Load the document, split it into chunks
raw_documents = TextLoader("db/in.txt").load()
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
documents = text_splitter.split_documents(raw_documents)
# embed each chunk and insert it into the vector store

db = PGVector.from_documents(documents, embeddings_model, connection=VG_CONN)
