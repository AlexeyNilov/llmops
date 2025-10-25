from data.sql_json import fetch, init_db
from conf.settings import RAW_SQL_DB_PATH


raw_conn = init_db(RAW_SQL_DB_PATH)


def fetch_issue(jira_key: str) -> str:
    data = fetch(raw_conn, jira_key)
    text = data["fields"]["summary"] + "\n" + str(data["fields"]["description"])
    return text
