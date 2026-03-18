#to create a user events table
from etl.warehouse import con

con.execute("CREATE TABLE IF NOT EXISTS user_events (id VARCHAR, user_id VARCHAR, article_id VARCHAR, event_type VARCHAR, session_id VARCHAR, timestamp TIMESTAMP, weight_applied FLOAT, source VARCHAR, PRIMARY KEY(id), FOREIGN KEY(user_id) REFERENCES user (user_id) )")