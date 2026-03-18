from enum import Enum

class EventType(Enum):
    ARTICLE_OPEN = 'article_open'
    ARTICLE_READ = 'article_read'
    ARTICLE_BOUNCE = 'article_bounce'
    ARTICLE_OPEN_FROM_CHATBOT = 'article_open_from_chatbot'

class Source(Enum):
    RAG_CHATBOT = "rag_chatbot"
    FEED = "feed"