'''
first the consumer reads path of the object from the redis streams
then from that path fetches the json from minio
after fetching from minio converts the json into a usable dictionary
then hands off the dictionary to the cleaner
cleaner hands off to enricher
enricher hands off to warehouse
once successfully inserted, sends an acknowledgement to redis saying "event consumed"
'''

import json
import boto3
from ingestion.lake_writer import db
import config
from etl.cleaner import cleaner
from etl.enricher import enrich
from etl.warehouse import insert_into_warehouse


# s3 client to fetch raw json files from minio
s3_client = boto3.client(
    "s3",
    endpoint_url=config.MINIO_ENDPOINT,
    aws_access_key_id=config.MINIO_USER,
    aws_secret_access_key=config.MINIO_PASSWORD
)

# stream names
STREAM_NAMES = ["raw/hackernews", "raw/arxiv", "raw/wikipedia","raw/latest_tech_news-writer","raw/tech_case_study-writer","raw/system-design-writer"]
CONSUMER_GROUP = "etl-workers"

# walrus ConsumerGroup takes ALL streams at once — not one stream at a time
# this is the correct walrus API: db.consumer_group(group_name, [list of stream names])
cg = db.consumer_group(CONSUMER_GROUP, STREAM_NAMES)
#cg.destroy()
# create the consumer group — wrap in try/except because it errors if already exists
try:
    cg.create()
    print(f"Consumer group '{CONSUMER_GROUP}' created for all streams")
except Exception:
    pass  # group already exists, move on


def fetch_from_minio(minio_path):
    '''fetch raw json file from minio and return as a python dictionary'''
    response = s3_client.get_object(Bucket=config.MINIO_BUCKET_RAW, Key=minio_path)
    raw_json = response["Body"].read().decode("utf-8")
    return json.loads(raw_json)


def process_message(stream_name, message_id, fields):
    '''
    takes one message from redis stream
    fetches from minio, cleans, enriches, loads into duckdb
    returns True if successful, False if rejected or failed
    '''
    # walrus returns bytes — decode all field keys and values
    fields = {
        k.decode() if isinstance(k, bytes) else k: v.decode() if isinstance(v, bytes) else v
        for k, v in fields.items()
    }

    minio_path = fields.get("minio_path")
    if not minio_path:
        print(f"[{stream_name}] No minio_path in message {message_id}, skipping")
        return False

    # fetch raw json from minio
    try:
        article_dict = fetch_from_minio(minio_path)
    except Exception as e:
        print(f"[{stream_name}] Failed to fetch from MinIO: {e}")
        return False

    # clean the article
    cleaned,msg = cleaner(article_dict)
    if cleaned is None:
        print(f"[{stream_name}] Article rejected by cleaner: {minio_path}")
        print(f"Reason : {msg}")
        return False

    # enrich the article
    try:
        article = enrich(cleaned)
    except Exception as e:
        print(f"[{stream_name}] Enrichment failed: {e}")
        return False

    # insert into duckdb warehouse
    try:
        insert_into_warehouse(article)
    except Exception as e:
        print(f"[{stream_name}] Warehouse insert failed: {e}")
        return False

    return True


def run():
    '''
    main consumer loop
    reads from all 3 streams simultaneously using cg.read()
    processes each message, acknowledges when done
    runs forever until interrupted
    '''
    print("ETL consumer started. Listening to streams...")

    while True:
        # cg.read() reads from ALL streams at once
        # returns: [('stream-name', [(msg_id, {fields})]), ...]
        # block=5000 — wait up to 5 seconds if no messages, then loop again
        results = cg.read(count=1, block=5000)

        if not results:
            continue  # no messages on any stream, loop again

        for stream_name, messages in results:
            # walrus returns stream names as bytes — decode
            if isinstance(stream_name, bytes):
                stream_name = stream_name.decode()

            for message_id, fields in messages:
                if isinstance(message_id, bytes):
                    message_id = message_id.decode()

                success = process_message(stream_name, message_id, fields)

                # get the specific stream object from consumer group and acknowledge
                # walrus exposes streams as attributes — raw/hackernews → cg.raw_hackernews
                stream_attr = stream_name.replace("/", "_").replace("-", "_")
                stream_obj = getattr(cg, stream_attr)
                stream_obj.ack(message_id)

                if success:
                    print(f"[{stream_name}] Successfully processed {message_id}")
                else:
                    print(f"[{stream_name}] Message {message_id} rejected or failed — acknowledged and skipped")


if __name__ == "__main__":
    run()