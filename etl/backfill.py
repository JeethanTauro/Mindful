#backfill is the file that takes already present data in duckdb and then embeds the data
#also we have to make sure that the is_embedding is set as true



from embedding.chunker import document_chunker
from embedding.loader import select_data_for_embedding
from embedding.store import add_chunks_to_collection
from embedding.embedder import get_embeddings
from etl_connection import con

#(id,source_id,source,url,title,author,content,word_count,reading_time,language,tags,published_at,scraped_at,processed_at,updated_at,embedding_id,)
def convert_into_dicts(list_of_rows):
    list_of_articles = []
    for row in list_of_rows:
        article_dict = {"id": row[0], "source": row[2], "url": row[3], "title": row[4], "author": row[5], "content": row[6]}
        list_of_articles.append(article_dict)
    return list_of_articles

if __name__ == '__main__':
    list_of_rows = select_data_for_embedding()
    list_of_articles = convert_into_dicts(list_of_rows)
    for article in list_of_articles:
        # chunk this article only
        try:
            chunks = document_chunker([article])

            # embed this article's chunks only
            sentences = [chunk.get("content") for chunk in chunks]
            embeddings = get_embeddings(sentences)

        # store each chunk
            for chunk, embedding in zip(chunks, embeddings):
                add_chunks_to_collection(chunk, embedding)

        # mark as embedded ONCE after all chunks stored
            con.execute( "UPDATE articles_warehouse SET is_embedded = TRUE WHERE id = ?",[article.get("id")])
            print(f"Embedded: {article.get('title')}")
        except Exception as e:
            print(f"Failed to embed {article.get('title')}: {e}")
            continue
    con.close()








