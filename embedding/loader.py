#loader basically loads the articles

'''
so basically we take each row from the duckdb and then return list of dicts
these dicts itself is our document from which we have to embed the
content
'''
import duckdb
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),"..", "data", "mindful.db")
con = duckdb.connect(DB_PATH)
def select_data_for_embedding():
    cur = con.cursor()
    result = cur.execute("SELECT * FROM articles_warehouse WHERE is_embedded = FALSE OR is_embedded IS NULL")
    list_of_rows = result.fetchall() #will return a list of tuple, one tuple is one row
    con.close()
    return list_of_rows
