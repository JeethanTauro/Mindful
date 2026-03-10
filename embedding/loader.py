#loader basically loads the articles

'''
so basically we take each row from the duckdb and then return list of dicts
these dicts itself is our document from which we have to embed the
content
'''
from etl.warehouse import con

def select_data_for_embedding():
    cur = con.cursor()
    result = cur.execute("SELECT * FROM articles_warehouse WHERE is_embedded = FALSE")
    list_of_rows = result.fetchall() #will return a list of tuple, one tuple is one row
    return list_of_rows
