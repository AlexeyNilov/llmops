import time
from langchain_core.documents import Document
from data.embedding import embed_docs, clean_up, get_vector_store
from data.sql_json import init_db, fetch_all
from data.issue import summarize_issue, get_title, fetch_issue_text
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
    jira_key = item["key"]
    print(f"Processing: {jira_key}")
    text = fetch_issue_text(jira_key)

    try:
        summary = summarize_issue(text)
    except TimeoutError as e:
        summary = ""
        print(e)

    text = get_title(jira_key) + "\n" + summary
    text = text.strip()

    print(f"Summary for {jira_key}: {text}")
    text_sum_len += len(text)
    docs.append(Document(page_content=text, metadata={"jira_key": jira_key}))
    c += 1
    print(f"Processed: {c}", end="\r")

print(f"Jira issues loaded: {c}")
print(f"Average text length: {round(text_sum_len / c, 0)}")

raw_conn.close()

stage = time.time()
print("Docs extracted", stage - init)

print(f"Docs count: {len(docs)}")

embed_docs(docs)

end = time.time()
print("Embedding completed", end - stage)
