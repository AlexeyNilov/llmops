from data.embedding import similarity_search, get_vector_store, clean_html
from data.sql_json import fetch, init_db
from conf.settings import RAW_SQL_DB_PATH, NEEDLE, CORRECT_ISSUES


raw_conn = init_db(RAW_SQL_DB_PATH)

data = fetch(raw_conn, NEEDLE)
text = data["fields"]["summary"]
text = clean_html(text)

vs = get_vector_store()
docs = similarity_search(vs=vs, query=text, k=10)

similar_issues = dict()
score = 0
for doc in docs:
    issues_key = doc.metadata["jira_key"]
    if issues_key not in similar_issues:
        similar_issues[issues_key] = 1
    else:
        similar_issues[issues_key] += 1

    if issues_key in CORRECT_ISSUES:
        score += 1

print(f"Score: {score}")
