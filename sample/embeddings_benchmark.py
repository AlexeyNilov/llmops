from data.embedding import similarity_search, get_vector_store, clean_html
from data.sql_json import fetch, init_db
from conf.settings import RAW_SQL_DB_PATH


raw_conn = init_db(RAW_SQL_DB_PATH)

needle = "ENV-118354"
correct_issues = ["ENV-116516", "ENV-114979", "ENV-116989"]

data = fetch(raw_conn, needle)
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

    if issues_key in correct_issues:
        score += 1

# print(similar_issues)
# print(f"Needle found: {needle in similar_issues.keys()}")
print(f"Score: {score}")
