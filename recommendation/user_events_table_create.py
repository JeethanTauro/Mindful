import duckdb, os
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),"..", "data", "mindful.db")
con = duckdb.connect(DB_PATH)
con.execute("DROP TABLE IF EXISTS user_events")
con.execute("""
    CREATE TABLE user_events (
        id VARCHAR,
        user_id VARCHAR,
        article_id VARCHAR,
        event_type VARCHAR,
        session_id VARCHAR,
        timestamp TIMESTAMP,
        weight_applied FLOAT,
        source VARCHAR,
        PRIMARY KEY(id)
    )
""")
con.close()
print("done")