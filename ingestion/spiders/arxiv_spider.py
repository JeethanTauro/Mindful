import arxiv

from ingestion.lake_writer import convert_into_json, upload
from ingestion.schema import RawArticle
import json
import boto3
from walrus import Database
from datetime import datetime
from time import sleep
from ingestion.schema import StreamEvent
import config


# categories you want
categories = [
        "cs.AI",     # Artificial Intelligence
        "cs.LG",     # Machine Learning
        "cs.CV",     # Computer Vision
        "cs.CL",     # Natural Language Processing
        "stat.ML"    # Statistical Machine Learning
    ]
def fetch_content():


    results = {}
    for category in categories:

        #constructs a search api
        search = arxiv.Search(
            query=f"cat:{category}",
            max_results=10,
            sort_by=arxiv.SortCriterion.SubmittedDate
        )

        #list of papers that
        papers = []

            #search.results gives list of pulled papers
        for paper in search.results():
            papers.append({
                "title": paper.title,
                "authors":", ".join([a.name for a in paper.authors]),
                "summary": paper.summary,
                "published": paper.published,
                "pdf_url": paper.pdf_url,
                "arxiv_id": paper.entry_id
            })

        #results will be of the form result { cs.AI : [list of papers]
        results[category] = papers
        sleep(1)
    return results


def map_to_schema(results):

    source = "arxiv"
    raw_articles = []

    for category, papers in results.items():

        for paper in papers:

            article = RawArticle(
                source=source,
                url=paper["pdf_url"],
                title=paper["title"],
                author=paper["authors"],
                content=paper["summary"],
                tags=[category],
                published_at=paper["published"]
            )

            raw_articles.append(article)

    return raw_articles


if __name__ == "__main__":
    results = fetch_content()
    print(results)
    print("\n")
    list_raw_articles = map_to_schema(results)
    print("\n")
    upload(list_raw_articles,"arxiv")
    print("uploaded to minio by arxiv spider")