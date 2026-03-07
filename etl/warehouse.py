'''
the final storage where the cleaned , enriched data that is stored
this is where the RAG will get the data from
'''
import duckdb

#created a table
con = duckdb.connect("data/mindful.db")
con.execute("CREATE TABLE IF NOT EXISTS articles_warehouse (id VARCHAR,source VARCHAR,url VARCHAR,title VARCHAR,author VARCHAR,content VARCHAR,word_count INTEGER,reading_time INTEGER, language VARCHAR, tags VARCHAR[],published_at DATETIME,scraped_at DATETIME, processed_at DATETIME,updated_at DATETIME,embedding_id VARCHAR )")


#if we are doing batch processing then i think we will get a list of articles here
def insert_into_warehouse(articles):
    for article in articles:
        con.execute("SELECT * FROM articles_warehouse WHERE url = ? ",[article.url])
        if con.fetchone() is None:
            con.execute("INSERT INTO articles_warehouse VALUES (?, ? , ? , ? , ? , ? , ? , ? , ? , ? , ? ,? , ? ,?,?)", (article.id,article.source,article.url,article.title,article.author,article.content,article.word_count,article.reading_time,article.language,article.tags,article.published_at,article.scraped_at,article.processed_at,article.updated_at,article.embedding_id))