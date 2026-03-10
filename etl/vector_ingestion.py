from embedding.chunker import document_chunker
from embedding.embedder import get_embeddings
from embedding.store import add_chunks_to_collection
def insert_into_vector_db(article):
    article_dict = {
        "id": article.id,
        "source": article.source,
        "url": article.url,
        "title": article.title,
        "author": article.author,
        "content": article.content
    }
    chunks = document_chunker([article_dict])
    sentences = [chunk.get("content") for chunk in chunks]
    embeddings = get_embeddings(sentences)
    for chunk, embedding in zip(chunks, embeddings):
        add_chunks_to_collection(chunk, embedding)
    print(f"Embedded: {article.title}")
