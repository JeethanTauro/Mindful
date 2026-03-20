
from fastapi import FastAPI
from rag.main import run
from pydantic import BaseModel
from recommendation.user_events_stream import push
from recommendation.user_table_insert import insert_user,user_exists,upsert_user
from recommendation.user_feed import get_user_feed,get_article_by_id


class Query(BaseModel):
    query : str
    memory : list = [] #client sends conversational history

class Events(BaseModel):
    user_id : str #user id is a foreign key , will get from the cookie
    article_id : str
    event_type :str
    session_id : str
    source : str

class User(BaseModel):
    user_id : str


app = FastAPI()

@app.get("/health")
async def health():
    return {"status": "ok"}


#rag chat
@app.post("/mindful/rag")
async def mindful_rag(q : Query):
    try:
        output  = run(query=q.query, memory=q.memory)
        return output
    except Exception as e:
        return {"status": "error", "message": str(e)}

#push event payload into streams
@app.post("/mindful/events")
async def mindful_events(e : Events):
    try:
        push(e)
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

#upsert the user
@app.post("/mindful/users")
async def mindful_users(u : User):
    try:
        if user_exists(u.user_id):
            upsert_user(u)
        else:
            insert_user(u)
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/mindful/recommendation")
async def mindful_recommendation(user_id: str):
    try:
        feed = get_user_feed(user_id)
        return feed
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.get("/mindful/article/{article_id}")
async def mindful_article(article_id: str):
    try:
        article = get_article_by_id(article_id)
        if not article:
            return {"status": "error", "message": "Article not found"}
        return article
    except Exception as e:
        return {"status": "error", "message": str(e)}
#wheneve the event is fired from this endpoint, it should run the user_events stream and put the event payload in the stream
#whenever the user first enters the website, immediately the user must be created in the db (because imagine if u user created is still in the stream and user is firing the events, the events have nothing to point in the database)