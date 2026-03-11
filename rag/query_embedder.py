
from embedding.embedder import get_embeddings
def embed_query(query):
    #the query is embedded and returns the embeddings list
    embeddings = get_embeddings([query])
    embeddings = embeddings[0].tolist()
    return embeddings
