from walrus import Database


def publish_to_redis_stream(event,db,stream_name):
    stream = db.Stream(stream_name)
    stream.add(event)
