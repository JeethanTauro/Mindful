import duckdb
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),"..", "data", "mindful.db")
con = duckdb.connect(DB_PATH)
