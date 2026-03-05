import dataclasses
from datetime import datetime
from time import sleep
import trafilatura
import requests
import config
from ingestion.schema import RawArticle, StreamEvent
import json
import boto3
from walrus import Database  # A subclass of the redis-py Redis client.
'''
first hit the api -> get 1000 ids
for each id:
    first inject it in the params of the item endpoint to get the details
    filter out the non story type because hacker news has , ask, poll, job, comment (this we can do using type)
        if it has text-> just take it as the content
        if it has url -> go to the url and then scrape the content using trafilatura
        if neither then skip the article
    handle the fetch failures gracefully using try except
    map to RawArticle
    sleep for 1 second (so that we respect the rate limiting)
now we have all the raw article objects
one by one write them to the raw bucket in minio and then publish event to stream
'''

#fetching the top and new stories and returning them in a list of lists
def fetch_ids():
    r_top_stories = requests.get(config.HACKER_TOP_STORIES)
    r_new_stories = requests.get(config.HACKER_NEW_STORIES)

    return [r_top_stories.json(), r_new_stories.json()]

#flatten the list of list and return the list of all ids
def flatten_list_ids(ids):

    list_ids = [item for sublist in ids for item in sublist]
    return list_ids

#build the item endpoint and for each id hit that endpoint
def hit_item_endpoint(list_ids):
    seen_ids = set()
    list_raw_articles = []
    item_endpoint = config.HACKER_NEWS_ITEM
    for id in list_ids:
        url = ""
        content=""
        title = ""
        author = ""
        if id not in seen_ids:
            seen_ids.add(id)
            endpoint = item_endpoint + f"{id}.json?print=pretty"
            #try to hit the endpoint
            try:
                r = requests.get(endpoint)
                if r.status_code == 200:
                    r = r.json()
                    #can be text or url but it has to be a story
                    if (r.get("text","") != " " or r.get("url","") != "") and r.get("type")=="story":
                        author = r.get("by","")
                        title = r.get("title","")
                        content  = r.get("text","")
                        # use trafilatura and get the content
                        if content == "":
                            url = r.get("url","")
                            try:
                                headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
                                response = requests.get(url, headers=headers, timeout=10)
                                content = trafilatura.extract(response.text) or ""

                            except Exception as e:
                                print(e)


                    #if both text and url are not there then skip this article id
                    else:
                        continue

                    raw = RawArticle(source="Hacker_News", url=url, title=title, author=author, content=content, tags=["hackernews"],
                             published_at=datetime.fromtimestamp(r["time"]) if r.get("time") else None)
                    list_raw_articles.append(raw)
                    sleep(1)
            except requests.exceptions.RequestException as e:
                print(e)
    return  list_raw_articles




#once we get the list of all the objects we can start storing first and publishing
#first convert the objects into dictionary
 #then convert the dictionary into jsonstring
#Upload that JSON string directly to MinIO under a path like: raw/hackernews/2024-01-15/article-uuid.json
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

#we need both dict and the json because json part becomes a string we cant access anything
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
        path =f"raw/hackernews/{dic_data.get('scraped_at')}/{dic_data.get('id')}" #uploading each of the file in its own path
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


        #if only successfully uploaded then push to stream
        if result is True:
            publish_to_redis_stream(event,db=db) #needed to convert the event into dict because add stream takes in dict


#i will be using walrus which is an extension of redis stream made by a developer
def publish_to_redis_stream(event,db):
    event = event.__dict__
    stream = db.Stream('raw/hackernews')
    stream.add(event)



if __name__ == "__main__":
    ids = fetch_ids() #fech ids
    print("fetched ids",ids)
    print("\n")
    print("\n")
    list_ids = flatten_list_ids(ids)
    print("flattened the list",list_ids)
    print("\n")
    print("\n")
    list_raw_articles =  hit_item_endpoint(list_ids)
    print("List of raw articles",list_raw_articles)
    print("\n")
    print("\n")
    list_json,list_dic = convert_into_json(list_raw_articles)
    upload(list_json,list_dic)
    print("Uploaded it in minio")




