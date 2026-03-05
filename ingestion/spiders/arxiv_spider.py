import arxiv

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

def convert_into_json(list_raw_articles):
    list_json = []
    list_dic=[]
    for raw in list_raw_articles:
        #convert each to dictionary and json stirng
        raw.scraped_at = raw.scraped_at.isoformat() #convertd the datetime object to string so that serialisation doesnt crash
        raw.published_at = raw.published_at.isoformat() if raw.published_at else None #same reason
        dic = raw.__dict__
        list_dic.append(dic)
        json_blob = json.dumps(dic)
        list_json.append(json_blob)
    return list_json,list_dic


def upload(list_json,list_dic):

    s3_client =  boto3.client(
        "s3",
        endpoint_url=config.MINIO_ENDPOINT,
        aws_access_key_id=config.MINIO_USER,
        aws_secret_access_key=config.MINIO_PASSWORD,
    )
    db =Database(host="localhost", port=config.REDIS_PORT)

    #iterating both list together using zip
    for json_data,dic_data in zip(list_json,list_dic):
        path =f"raw/arxiv/{dic_data.get('scraped_at')}/{dic_data.get('id')}" #uploading each of the file in its own path
        event = StreamEvent(event_type="raw_article_stored", article_id=dic_data.get("id"), minio_path=path,
                            source=dic_data.get("source"))
        try:
            result = s3_client.put_object(Bucket='raw',Key=path, Body=json_data) #try for the minio uploading
            for attempt in range(4):
                try:
                    publish_to_redis_stream(event, db) #try for redis upload
                    break
                except:
                    if attempt == 3:
                        print("failed to upload to redis")
                    else:
                        sleep(1) #if attempts failed try again after some time
        except Exception as e:
            print(e)

        publish_to_redis_stream(event,db=db) #needed to convert the event into dict because add stream takes in dict


#i will be using walrus which is an extension of redis stream made by a developer
def publish_to_redis_stream(event,db):
    event = event.__dict__
    stream = db.Stream('raw/arxiv')
    stream.add(event)


if __name__ == "__main__":
    results = fetch_content()
    print(results)
    print("\n")
    list_raw_articles = map_to_schema(results)
    list_json,list_dic = convert_into_json(list_raw_articles)
    print(list_dic)
    print("\n")
    upload(list_json,list_dic)
    print("uploaded to minio")