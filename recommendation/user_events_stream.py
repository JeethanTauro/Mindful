#whenever the user does an action the first thing is that it must go to event stream
import config
from ingestion.stream_publisher import publish_to_redis_stream
from walrus import Database


db = Database(host="localhost", port=config.REDIS_PORT)

def push(e):
    print(f"Pushing event to stream: {e.model_dump()}")
    publish_to_redis_stream(event=e.model_dump(),db=db,stream_name="events/user_interactions")
