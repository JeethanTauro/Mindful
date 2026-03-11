from sentence_transformers import CrossEncoder

reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")


def rerank(query, chunks, metadatas, top_k=5):
    # build (query, chunk_text) pairs
    pairs = [(query, chunk) for chunk in chunks]

    # score all pairs simultaneously
    scores = reranker.predict(pairs)

    # zip chunks with their scores and metadata
    scored = list(zip(chunks, metadatas, scores))

    # sort by score descending
    scored.sort(key=lambda x: x[2], reverse=True)

    # return top k
    top_chunks = [item[0] for item in scored[:top_k]]
    top_metadatas = [item[1] for item in scored[:top_k]]

    return top_chunks, top_metadatas