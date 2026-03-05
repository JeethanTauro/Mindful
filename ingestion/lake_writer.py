import json
from time import sleep

import boto3
import config
from walrus import Database

from ingestion.schema import StreamEvent
from ingestion.stream_publisher import publish_to_redis_stream


db = Database(host="localhost", port=config.REDIS_PORT)
s3_client = boto3.client(
    "s3",
    endpoint_url=config.MINIO_ENDPOINT,
    aws_access_key_id=config.MINIO_USER,
    aws_secret_access_key=config.MINIO_PASSWORD,
)


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

def upload(list_raw_articles,spider):
    list_json,list_dic = convert_into_json(list_raw_articles)



    #iterating both list together using zip
    for json_data,dic_data in zip(list_json,list_dic):
        path =f"raw/{spider}/{dic_data.get('scraped_at')}/{dic_data.get('id')}" #uploading each of the file in its own path
        event = StreamEvent(event_type="raw_article_stored", article_id=dic_data.get("id"), minio_path=path,
                            source=dic_data.get("source"))
        try:
            s3_client.put_object(Bucket='raw',Key=path, Body=json_data) #try for the minio uploading
            for attempt in range(4):
                try:
                    publish_to_redis_stream(event, db,f"raw/{spider}") #try for redis upload
                    break
                except:
                    if attempt == 3:
                        print("failed to upload to redis")
                    else:
                        sleep(1) #if attempts failed try again after some time
        except Exception as e:
            print(e)