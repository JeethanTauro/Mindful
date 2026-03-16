#this is the main file that wires all together

from rag.query_enhancer import enhancer
from rag.query_embedder import embed_query
from rag.guard import guard
from rag.similarity_search import search
from rag.reranker import  rerank
from rag.context_builder import context_builder
from rag.chat import llm_chat
from rag.router import router
from rag.casual_query import casual_query

def run(query,memory):
    if memory is None:
        memory = []

    safe, msg = guard(query)
    if not safe:
        return {"answer": msg, "safe": False, "sources": []}

    route = router(query)
    if route == "CASUAL_QUERY":
        return casual_query(query,memory)


    enhanced_query = enhancer(query, memory)
    embeddings = embed_query(enhanced_query)
    chunks, metadata = search(embeddings=embeddings)
    chunks, metadata = rerank(enhanced_query, chunks[0], metadata[0])
    context = context_builder(chunks, metadata, enhanced_query)
    output = llm_chat(context, memory)

    return {"answer": output, "safe": True, "sources":context["sources"]}




