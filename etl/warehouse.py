'''
the final storage where the cleaned , enriched data that is stored
this is where the RAG will get the data from
'''
import duckdb
import os

#created a table
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),"..", "data", "mindful.db")
con = duckdb.connect(DB_PATH)
# con.execute("CREATE TABLE IF NOT EXISTS articles_warehouse (id VARCHAR,source_id VARCHAR,source VARCHAR,url VARCHAR,title VARCHAR,author VARCHAR,content VARCHAR,word_count INTEGER,reading_time INTEGER, language VARCHAR, tags VARCHAR[],published_at DATETIME,scraped_at DATETIME, processed_at DATETIME,updated_at DATETIME,embedding_id VARCHAR )")


#if we are doing stream processing one article at a time
def insert_into_warehouse(article):
    if article.url:
        # normal case — deduplicate by URL
        con.execute("SELECT * FROM articles_warehouse WHERE url = ?", [article.url])
    else:
        # text-only HN articles — deduplicate by source_id
        con.execute("SELECT * FROM articles_warehouse WHERE source_id = ?", [article.source_id])
    if con.fetchone() is None:
        con.execute("INSERT INTO articles_warehouse VALUES ( ?, ? , ? , ? , ? , ? , ? , ? , ? , ? , ? ,? , ? , ? , ? , ? )", (article.id,article.source_id,article.source,article.url,article.title,article.author,article.content,article.word_count,article.reading_time,article.language,article.tags,article.published_at,article.scraped_at,article.processed_at,article.updated_at,article.embedding_id))

