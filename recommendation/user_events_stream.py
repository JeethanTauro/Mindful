#whenever the user does an action the first thing is that it must go to event stream
import config
from ingestion.stream_publisher import publish_to_redis_stream
from walrus import Database


db = Database(host="localhost", port=config.REDIS_PORT)

def push(e):
    publish_to_redis_stream(event=e,db=db,stream_name="events/user_interactions")
