from data.embedding import similarity_search, get_vector_store
from data.issue import summarize_issue, get_title, fetch_issue_text
from conf.settings import NEEDLE, CORRECT_ISSUES

text = fetch_issue_text(NEEDLE)
summary = summarize_issue(text)
text = get_title(NEEDLE) + "\n" + summary

vs = get_vector_store()
docs = similarity_search(vs=vs, query=text, k=10)

similar_issues = dict()
score = 0
for doc in docs:
    issues_key = doc.metadata["jira_key"]
    similar_issues[issues_key] = get_title(issues_key)

    if issues_key in CORRECT_ISSUES:
        score += 1


print(similar_issues.keys())
print(f"Similar issues found: {len(similar_issues)}")
print(f"Score: {score}, expected {len(CORRECT_ISSUES)}")
