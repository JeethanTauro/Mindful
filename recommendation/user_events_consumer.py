import socket
import os
import numpy as np
import duckdb
from recommendation.user_events_stream import db
from recommendation.enums import EventType

CONSUMER_NAME = f"worker-{socket.gethostname()}"
# unique name per machine so if you scale to multiple workers they don't clash

CONSUMER_GROUP = "event-consumer"
# group name — Redis uses this to track which messages have been processed

EVENT_WEIGHTS = {
EventType.ARTICLE_OPEN.value: 0.3,
    EventType.ARTICLE_READ.value: 0.8,
    EventType.ARTICLE_BOUNCE.value: -0.2,
    EventType.ARTICLE_OPEN_FROM_CHATBOT.value: 0.6,
}
# centralised weight map — single source of truth, easy to tune later

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "mindful.db")
# resolves to absolute path of mindful.db regardless of where you run the script from

CHROMA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "chroma")
# same pattern for chroma

import chromadb
chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
collection = chroma_client.get_collection("mindful_articles")
# get the existing collection — don't create, it must already exist from embedding pipeline

cg = db.consumer_group(CONSUMER_GROUP, ["events/user_interactions"])
try:
    cg.create()
    print(f"Consumer group '{CONSUMER_GROUP}' created")
except Exception:
    pass


def decode_fields(fields):
    # walrus returns bytes — decode everything to strings
    return {
        k.decode() if isinstance(k, bytes) else k: v.decode() if isinstance(v, bytes) else v
        for k, v in fields.items()
    }


def fetch_article_embedding(article_id):
    result = collection.get(
        where={"article_id": article_id},
        include=["embeddings"]
    )
    if result["embeddings"] is None or len(result["embeddings"]) == 0:
        return None
    # average all chunk embeddings to get a single article-level vector
    return np.mean(np.array(result["embeddings"]), axis=0)

def fetch_user(con, user_id):
    # fetch the user's current row from duckdb
    result = con.execute("SELECT interest_vector, event_count FROM users WHERE user_id = ?", (user_id,)).fetchone()
    return result
    # returns (interest_vector, event_count) tuple or None if user doesn't exist


def compute_new_vector(existing_vector, article_vector, weight):
    if existing_vector is None:
        # cold start — article vector becomes the interest vector directly
        return article_vector

    existing = np.array(existing_vector)
    # weighted moving average — pulls vector toward or away from article
    updated = (existing * (1 - abs(weight))) + (article_vector * weight)
    # normalize to unit length — critical for cosine similarity in chroma to work correctly
    norm = np.linalg.norm(updated)
    if norm == 0:
        return updated
    return updated / norm


def update_user(con, user_id, new_vector, new_event_count):
    from datetime import datetime
    is_cold = new_event_count < 5
    # flip cold flag once they cross threshold
    now = datetime.now()
    con.execute("""
        UPDATE users SET
            interest_vector = ?,
            event_count = ?,
            is_cold = ?,
            last_seen_at = ?,
            vector_updated_at = ?
        WHERE user_id = ?
    """, (new_vector.tolist(), new_event_count, is_cold, now, now, user_id))
    # tolist() converts numpy array to plain python list — duckdb can't take numpy arrays directly


def insert_event(con, fields, weight):
    from datetime import datetime
    import uuid
    con.execute("""
        INSERT INTO user_events VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        str(uuid.uuid4()),       # generate event id server side
        fields["user_id"],
        fields["article_id"],
        fields["event_type"],
        fields["session_id"],
        datetime.now(),          # timestamp generated here not from client
        weight,                  # weight applied stored for audit
        fields["source"]
    ))
    # permanent immutable record — written before user row update intentionally


def process_event(fields):
    user_id = fields["user_id"]
    article_id = fields["article_id"]
    event_type = fields["event_type"].strip()

    weight = EVENT_WEIGHTS.get(event_type)
    if weight is None:
        print(f"Unknown event type: {event_type}, skipping")
        return False
    # unknown event type — skip rather than crash

    article_vector = fetch_article_embedding(article_id)
    if article_vector is None:
        print(f"Article {article_id} not found in chroma, skipping vector update")
        return False
    # article must exist in chroma — if not, nothing to update vector with

    con = duckdb.connect(DB_PATH)
    # open fresh connection per event — releases lock immediately after done

    try:
        user_row = fetch_user(con, user_id)
        if user_row is None:
            print(f"User {user_id} not found in db, skipping")
            return False

        existing_vector, event_count = user_row
        new_vector = compute_new_vector(existing_vector, article_vector, weight)
        new_event_count = event_count + 1

        insert_event(con, fields, weight)
        # write event first — so if user update crashes, event is still recorded

        update_user(con, user_id, new_vector, new_event_count)
        # update user row after event is safely written

        return True
    except Exception as e:
        print(f"Failed to process event: {e}")
        return False
    finally:
        con.close()
        # always close — even if exception occurs


MAX_RETRIES = 3
DEAD_LETTER_STREAM = "events_dead_letter"
# after 3 failed attempts, message moves here permanently for manual inspection

def move_to_dead_letter(message_id, fields):
    dead_stream = db.Stream(DEAD_LETTER_STREAM)
    fields["failed_message_id"] = message_id
    fields["reason"] = "exceeded max retries"
    dead_stream.add(fields)
    print(f"Message {message_id} moved to dead letter stream")
    # preserves the original payload so you can debug or replay manually later

def process_pending():
    stream = cg.events_user_interactions
    result = stream.autoclaim(
        CONSUMER_NAME,
        min_idle_time=30000,  # reclaim messages idle for 30 seconds
        start_id="0-0",
        count=10
    )
    if not result:
        return

    next_id, messages, deleted_ids = result

    for message_id, fields in messages:
        if isinstance(message_id, bytes):
            message_id = message_id.decode()

        fields = decode_fields(fields)

        # check how many times this message has been delivered
        pending_info = stream.pending(consumer=CONSUMER_NAME)
        delivery_count = next(
            (p["times_delivered"] for p in pending_info
             if (p["message_id"].decode() if isinstance(p["message_id"], bytes) else p["message_id"]) == message_id),
            0
        )

        if delivery_count >= MAX_RETRIES:
            move_to_dead_letter(message_id, fields)
            stream.ack(message_id)
            # ack it so redis stops redelivering — it's in dead letter now
            continue

        success = process_event(fields)
        if success:
            stream.ack(message_id)
            print(f"Retried pending {message_id} successfully")
        else:
            print(f"Pending {message_id} failed again — attempt {delivery_count}/{MAX_RETRIES}")


def run():
    print("Event consumer started. Listening on events/user_interactions...")
    stream = cg.events_user_interactions
    # walrus converts stream name slash/underscore to attribute name

    process_pending()
    while True:
        results = cg.read(count=10, block=5000)
        # block=5000 means wait up to 5 seconds for new messages before looping
        # count=10 means process up to 10 messages per read

        if not results:
            continue

        for stream_name, messages in results:
            for message_id, fields in messages:
                if isinstance(message_id, bytes):
                    message_id = message_id.decode()

                fields = decode_fields(fields)
                success = process_event(fields)

                if success:
                    stream.ack(message_id)
                    # ack only after both db writes succeeded
                    print(f"Processed event {message_id} for user {fields['user_id']}")
                else:
                    print(f"Failed event {message_id} — left pending for retry")
                    # not acking means Redis will redeliver on next autoclaim


if __name__ == "__main__":
    run()