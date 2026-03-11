#this is the main file that wires all together
from query_from_user import user_query
from query_enhancer import enhancer
from query_embedder import embed_query
from rag.guard import guard
from similarity_search import search
from reranker import  rerank
from context_builder import context_builder
from chat import llm_chat
if __name__ == '__main__':
    memory = []
    while True:
        query = user_query() #taking the user query

        safe, msg = guard(query)
        if not safe:
            print(f"Mindful: {msg}")
            continue

        enhanced_query= enhancer(query,memory) #enchancing it according to memory

        embeddings = embed_query(enhanced_query) #get embeddings of the query

        chunks,metadata = search(embeddings=embeddings) #from the query get the chunks and metadata

        chunks,metadata = rerank(enhanced_query,chunks[0],metadata[0])#reranking the chunks

        context = context_builder(chunks,metadata,enhanced_query) #building the context for the chatbot

        output = llm_chat(context,memory) #output after prompt

        #building the memory
        memory.append({"role": "user", "content": query})
        memory.append({"role": "assistant", "content": output})
        print(output)



