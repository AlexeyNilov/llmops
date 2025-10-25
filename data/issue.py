from data.sql_json import fetch, init_db
from data.sum import summarize_text
from conf.settings import RAW_SQL_DB_PATH


raw_conn = init_db(RAW_SQL_DB_PATH)


def fetch_issue(jira_key: str) -> str:
    data = fetch(raw_conn, jira_key)
    text = data["fields"]["summary"] + "\n" + str(data["fields"]["description"])
    return text


def summarize_issue(jira_key: str) -> str:
    text = fetch_issue(jira_key)
    text = text[:500]
    text = summarize_text(text)
    text = text[:256]
    return text
