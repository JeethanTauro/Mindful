#whenever a new user is created it must be ingested as a new row in duckdb
from datetime import datetime

from etl.warehouse import con

def user_exists(user_id):
    con.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    if con.fetchone():
        return True
    return False


def insert_user(user):
    #user id already set by client
    user.interest_vector = None #no interest vector intiially as the evnts havent been processed by the consumer
    user.created_at = datetime.now() # created will never change
    user.event_count = 0 #initially 0
    user.last_seen_at = datetime.now() #current time
    user.is_cold = True #as there are no events generated
    user.vector_updated_at = None #no meaningful vector update
    con.execute("INSERT INTO users VALUES ( ?,?,?,?,?,?,?)",
                (user.user_id, user.interest_vector, user.created_at, user.last_seen_at, user.event_count, user.is_cold,
                 user.vector_updated_at))

def upsert_user(user):
    user.last_seen_at = datetime.now()
    con.execute("UPDATE users SET last_seen_at = ? WHERE user_id = ?",(user.user_id,))
    """
    interest_vector → gets updated by the consumer worker, not here
    event_count → gets incremented by the consumer worker after each event
    is_cold → gets recalculated by the consumer worker
    vector_updated_at → gets updated by the consumer worker
    created_at → never changes, it's immutable
    """



