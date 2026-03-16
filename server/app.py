from fastapi import FastAPI
from rag.main import run
from pydantic import BaseModel


class Query(BaseModel):
    query : str
    memory : list = [] #client sends conversational history

app = FastAPI()

@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/mindful/rag")
async def mindful_rag(q : Query):
    output  = run(query=q.query, memory=q.memory)
    return output

