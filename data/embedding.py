from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_postgres.vectorstores import PGVector
from conf.settings import VG_CONN
import urllib3
import re
from langchain_ollama import OllamaEmbeddings


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

MODEL_NAME = "nomic-embed-text"
EM = OllamaEmbeddings(model=MODEL_NAME)


def clean_html(text: str) -> str:
    # Remove Jira/Confluence markup like {code}, {panel}, etc.
    text = re.sub(r"\{.*?\}", " ", text)
    return text.lower().strip()


def get_vector_store() -> PGVector:
    return PGVector.from_existing_index(embedding=EM, connection=VG_CONN)


def embed_docs(documents: list) -> PGVector:
    return PGVector.from_documents(documents, EM, connection=VG_CONN)


def similarity_search(vs: PGVector, query: str, k: int = 5):
    return vs.similarity_search(query, k=k)


def clean_up(vs: PGVector):
    vs.delete_collection()


def split_docs(docs: list) -> list:
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    return text_splitter.split_documents(docs)
