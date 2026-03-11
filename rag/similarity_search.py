from importlib.metadata import metadata

from embedding.store import collection
def search(embeddings):
    #using the query embedding top 10 similar chunks from the vector db is retrieved
    #returns a list of all the chunks

    #the query returns a huge dict (check docs of chroma db)
    dicts_of_data = collection.query(
        query_embeddings= [embeddings],
        n_results=20
    )
    #documents that were retrieved im assuming, the docs is the chunks
    chunks = dicts_of_data.get("documents") #documents = [["",""]]
    metadata = dicts_of_data.get("metadatas") # metadata = [[{} , {} ]] and the corresponding chunks have the metada
    return chunks, metadata



