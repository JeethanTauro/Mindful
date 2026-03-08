'''
The enricher basically adds meaningful data used by the downstream services, like the word count, average estimated time
to read the article, the language of the article and some more data
'''
import datetime
import math
import re
import langdetect

from etl.schema import ArticleSchema


def count_words(content):
    words = re.findall(r'\b\w+\b', content)
    return len(words)

#take dict, add fields, convert to Article
def enrich(article_dict):
    words = count_words(article_dict['content'])
    article_dict['word_count'] = words
    article_dict['reading_time'] = math.ceil(words / 200)
    try:
        article_dict['language'] = langdetect.detect(article_dict['content'])
    except:
        article_dict['language'] = "unknown"
    article_dict['processed_at'] = datetime.datetime.now()
    article_dict['updated_at'] = article_dict['processed_at']
    article = ArticleSchema(source=article_dict.get("source"), source_id=article_dict.get("source_id"), url=article_dict.get("url"), title=article_dict.get("title"), author=article_dict.get("author"),word_count=article_dict.get("word_count"), reading_time=article_dict.get("reading_time"),language=article_dict.get("language"),content=article_dict.get("content"),tags=article_dict.get("tags"), scraped_at=article_dict.get("scraped_at"), published_at=article_dict.get("published_at"), processed_at=article_dict.get("processed_at"),updated_at=article_dict.get("updated_at"), embedding_id=None)
    return article