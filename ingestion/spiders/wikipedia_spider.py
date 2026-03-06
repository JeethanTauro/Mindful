from time import sleep

import wikipedia

from ingestion.lake_writer import upload
from ingestion.schema import RawArticle

categories = [
    "Machine learning",
    "Artificial Intelligence",
    "Cybersecurity",
    "Programming Languages",
]
'''
"Distributed systems",
    "Data Science",
    "Agentic AI",
    "Database Systems",
    "Cloud technology",
    "Neural Networks",
    "Natural Language Processing"
'''
def fetch_pages():
    list_of_pages=[]
    for category in categories:
        try:
            list_titles = wikipedia.search(category)[:5]
            for title in list_titles:
                try:
                    page = wikipedia.page(title)
                except wikipedia.DisambiguationError:
                    continue  # skip this title, move to next
                except wikipedia.PageError:
                    continue  # page doesn't exist, skip
                except Exception as e:
                    print(e)
                    continue
                list_of_pages.append(page)
                sleep(1)
        except Exception as e:
            print(e)
    return list_of_pages

def map_to_schema(list_of_pages):
    list_raw_articles=[]
    for page in list_of_pages:
        raw_article = RawArticle(source="wikipedia", title=page.title,author="wikipedia",content=page.summary,url=page.url,tags=page.categories[:5] ,published_at=None)
        list_raw_articles.append(raw_article)
    return list_raw_articles


if __name__ == "__main__":
    pages = fetch_pages()
    print(pages)
    print("\n")
    list_raw_articles = map_to_schema(pages)[:5]
    upload(list_raw_articles,"wikipedia")
    print("uploaded to minio by wikipedia spider")




