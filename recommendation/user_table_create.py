#to create a user table
import os
import duckdb
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),"..", "data", "mindful.db")

con = duckdb.connect(DB_PATH)
con.execute("CREATE TABLE IF NOT EXISTS users (user_id VARCHAR, interest_vector FLOAT[384], created_at TIMESTAMP, last_seen_at TIMESTAMP, event_count INTEGER, is_cold BOOLEAN, vector_updated_at TIMESTAMP, PRIMARY KEY(user_id) )")
con.close()