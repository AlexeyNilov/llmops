from data.sql_json import fetch, init_db
from data.sum import summarize_text
from conf.settings import RAW_SQL_DB_PATH, NEEDLE
import time


raw_conn = init_db(RAW_SQL_DB_PATH)

data = fetch(raw_conn, NEEDLE)
text = data["fields"]["summary"] + "\n" + data["fields"]["description"]

start = time.time()
print(summarize_text(text))

end = time.time()
print("Time taken: ", end - start)
