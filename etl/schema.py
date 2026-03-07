import uuid

class ArticleSchema:
    def __init__(self,source,url,title,author, word_count, reading_time, language ,content,tags, scraped_at ,published_at, processed_at,embedding_id ):
        self.id = str(uuid.uuid4())
        self.source = source
        self.url = url
        self.title = title
        self.author = author
        self.content = content
        self.word_count = word_count
        self.reading_time = reading_time
        self.language = language
        self.tags = tags
        self.published_at = published_at
        self.scraped_at = scraped_at
        self.processed_at = processed_at
        self.embedding_id = embedding_id



