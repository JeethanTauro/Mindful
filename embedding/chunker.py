#this file basically breaks the article for embedding
#so yeah this is chunking

from langchain_text_splitters import RecursiveCharacterTextSplitter


def document_chunker(list_of_articles):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    list_of_chunks_with_metadata_per_article = []
    for article in list_of_articles:
        chunk_index = 0
        content = article.get("content") #get the content of the article to be chunked
        texts = text_splitter.split_text(content) #gives list of divided text
        for text in texts:
            chunk_index += 1
            chunks_dict = {"id" :article.get("id"), "source": article.get("source"), "author":article.get("author"), "title":article.get("title"), "url":article.get("url"),"chunk_index":chunk_index,"content":text}
            list_of_chunks_with_metadata_per_article.append(chunks_dict)

    return list_of_chunks_with_metadata_per_article




