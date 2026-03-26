# Mindful

An intelligent content platform that learns what you care about and personalises your feed over time.

---

## What is Mindful?

Mindful is a full-stack async data intelligence platform that ingests articles from across the web, lets you chat with the content via a RAG-powered chatbot, and continuously learns your interests to serve a personalised feed — all without requiring you to create an account.

---

## What does it do?

- **Ingests content** from scrapers (HackerNews, ArXiv, Wikipedia) and AI writers covering tech, finance, psychology, science, career, and more
- **Processes and enriches** articles through a cleaning and enrichment ETL pipeline
- **Embeds articles** into a vector store for semantic search
- **Serves a personalised feed** that adapts based on how you interact with articles — what you open, read, bounce from, or discover through the chatbot
- **RAG chatbot** that answers questions grounded in the article corpus and links you directly to source articles
- **Anonymous by default** — identity is a UUID cookie, no sign-up required

---

## Systems Used

| Layer | Technology |
|---|---|
| Scraping | Scrapy |
| AI Writers | Claude (Anthropic) via compound-beta |
| Object Storage | MinIO (S3-compatible) |
| Message Streaming | Redis Streams (via Walrus) |
| Data Warehouse | DuckDB |
| Vector Store | ChromaDB |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2) |
| LLM | Groq |
| Backend API | FastAPI |
| Frontend | Streamlit |

---

## Architecture Overview

```
Scrapers + AI Writers
        ↓
     MinIO (raw storage)
        ↓
   Redis Streams
        ↓
  ETL Consumer → DuckDB + ChromaDB
        ↓
     FastAPI
        ↓
    Streamlit
        ↑
  Event Consumer ← Redis Streams ← User Interactions
```

---

## How to Run

**Prerequisites:** Redis, MinIO, and Python 3.12+ must be running.

```bash
# Install dependencies
pip install -r requirements.txt

# Run all components (separate terminals)
PYTHONPATH=. fastapi run server/app.py          # API server
PYTHONPATH=. python etl/consumer.py             # ETL pipeline
PYTHONPATH=. python recommendation/user_events_consumer.py  # Event consumer
streamlit run frontend/Home.py                  # Frontend
```

---

## Future Work

-  Redis cache layer for feed reads
-  Micro-batching buffer for DuckDB article writes
-  Collaborative filtering using HDBSCAN clustering on interest vectors
-  Observability — structured logging and Prometheus metrics
