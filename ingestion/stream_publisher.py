from walrus import Database


def publish_to_redis_stream(event,db,stream_name):
    event = event.__dict__
    stream = db.Stream(stream_name)
    stream.add(event)
