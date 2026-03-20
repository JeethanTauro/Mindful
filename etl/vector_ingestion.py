from embedding.chunker import document_chunker
from embedding.embedder import get_embeddings
from embedding.store import add_chunks_to_collection
import os
import duckdb

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),"..", "data", "mindful.db")

def insert_into_vector_db(article):
    article_dict = {
        "id": article.id,
        "source": article.source,
        "url": article.url,
        "title": article.title,
        "author": article.author,
        "content": article.content
    }
    try:
        chunks = document_chunker([article_dict])
        sentences = [chunk.get("content") for chunk in chunks]
        embeddings = get_embeddings(sentences)
        for chunk, embedding in zip(chunks, embeddings):
            add_chunks_to_collection(chunk, embedding)

        # mark as embedded in duckdb after all chunks stored successfully
        con = duckdb.connect(DB_PATH)
        try:
            con.execute("UPDATE articles_warehouse SET is_embedded = TRUE WHERE id = ?", [article.id])
        finally:
            con.close()

        print(f"Embedded: {article.title}")
    except Exception as e:
        print(f"Failed to embed article {article.title}: {e}")
        # dont re-raise — let ETL consumer decide whether to retry via stream