import time
from langchain_core.documents import Document
from data.embedding import embed_docs, clean_up, get_vector_store, clean_html
from data.sql_json import init_db, fetch_all
from conf.settings import RAW_SQL_DB_PATH


start = time.time()
print("Started")

raw_conn = init_db(RAW_SQL_DB_PATH)
clean_up(get_vector_store())

init = time.time()
print("Init done", init - start)

docs = list()

c = 0
text_sum_len = 0
for _, _, item in fetch_all(raw_conn):
    text = item["fields"]["summary"]  # + "\n" + str(item["fields"]["description"])
    text = clean_html(text)
    text_sum_len += len(text)
    docs.append(Document(page_content=text, metadata={"jira_key": item["key"]}))
    c += 1

print(f"Jira issues loaded: {c}")
print(f"Average text length: {round(text_sum_len / c, 0)}")

raw_conn.close()

stage = time.time()
print("Docs extracted", stage - init)

print(f"Docs count: {len(docs)}")

embed_docs(docs)
# embed_docs(docs[2000:3000])

end = time.time()
print("Embedding completed", end - stage)
