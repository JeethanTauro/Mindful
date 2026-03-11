#now once u get the embedding store it in the vector store
import chromadb
from etl.warehouse import con
import uuid
import os

CHROMA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),"..", "data", "chroma")
client = chromadb.PersistentClient(CHROMA_PATH)
collection = client.get_or_create_collection("mindful_articles")

def add_chunks_to_collection(chunk_with_metadata,embeddings):
    collection.add(
        embeddings=[embeddings.tolist()] ,
        documents=[chunk_with_metadata.get("content")],
        metadatas=[{ "article_id": chunk_with_metadata.get("id"), "source": chunk_with_metadata.get("source"), "title": chunk_with_metadata.get("title"),"author":chunk_with_metadata.get("author"),"url":chunk_with_metadata.get("url"),"chunk_index":chunk_with_metadata.get("chunk_index")}],
        ids=[str(uuid.uuid4())],
    )
