#to create a user table
from etl.warehouse import con

con.execute("CREATE TABLE IF NOT EXISTS user (user_id VARCHAR, interest_vector FLOAT[384], created_at TIMESTAMP, last_seen_at TIMESTAMP, event_count INTEGER, is_cold BOOLEAN, vector_updated_at TIMESTAMP, PRIMARY KEY(user_id) )")