#whenever a new user is created it must be ingested as a new row in duckdb
from datetime import datetime
import duckdb
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),"..", "data", "mindful.db")


def user_exists(user_id):
    con = duckdb.connect(DB_PATH)
    con.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    result = con.fetchone()
    con.close()
    if result:
        return True
    return False



def insert_user(user):
    con = duckdb.connect(DB_PATH)
    try:
        now = datetime.now()
        con.execute("INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, ?)", (
            user.user_id, None, now, now, 0, True, None
        ))
    finally:
        con.close()

def upsert_user(user):
    con = duckdb.connect(DB_PATH)
    try:
        con.execute("UPDATE users SET last_seen_at = ? WHERE user_id = ?", (
            datetime.now(), user.user_id
        ))
    finally:
        con.close()



