from data.sql_json import fetch, init_db
from data.sum import summarize_text
from lib.timeout import with_timeout
from conf.settings import RAW_SQL_DB_PATH


DB_CONNECTION = init_db(RAW_SQL_DB_PATH)
TEXT_LIMIT = 500


def fetch_issue_text(jira_key: str) -> str:
    data = fetch(DB_CONNECTION, jira_key)
    text = data["fields"]["summary"] + "\n" + str(data["fields"]["description"])
    return text


@with_timeout(timeout=2.0)
def summarize_issue(text: str, limit: int = TEXT_LIMIT) -> str:
    middle = limit // 2
    if len(text) > limit:
        text = (
            text[:middle] + "\n" + text[-middle:]
        )  # We hope that beginnings and endings have the most important info

    text = summarize_text(text)
    text = text[:256]  # Truncate to avoid overly long summaries
    return text


def get_title(jira_key: str) -> str:
    data = fetch(DB_CONNECTION, jira_key)
    return data["fields"]["summary"]
