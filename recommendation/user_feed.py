import os
import chromadb
import duckdb

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "mindful.db")

CHROMA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "chroma")
client = chromadb.PersistentClient(CHROMA_PATH)
collection = client.get_or_create_collection("mindful_articles")


def get_user_feed(user_id):
    con = duckdb.connect(DB_PATH, read_only=True)
    try:
        user_df = con.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchdf()
        user = user_df.iloc[0].to_dict() if not user_df.empty else None
    finally:
        con.close()

    if user is None or user["is_cold"]:
        return global_feed()
    else:
        return personalised_feed(user)


def global_feed():
    con = duckdb.connect(DB_PATH, read_only=True)
    try:
        rows = con.execute("""
            SELECT id, title, author, source, word_count, reading_time,
                   published_at, content, scraped_at
            FROM articles_warehouse
            ORDER BY published_at DESC
            LIMIT 30
        """).fetchdf()
        return rows.to_dict(orient="records")
    finally:
        con.close()


def fetch_articles_by_ids(ids):
    con = duckdb.connect(DB_PATH, read_only=True)
    try:
        placeholders = ",".join(["?" for _ in ids])
        rows = con.execute(f"""
            SELECT id, title, author, source, word_count, reading_time,
                   published_at, content, scraped_at
            FROM articles_warehouse
            WHERE id IN ({placeholders})
        """, ids).fetchdf()
        return rows.to_dict(orient="records")
    finally:
        con.close()


def personalised_feed(user):
    feed_size = 30
    personalized_count = 18  # 60%
    fresh_count = 9           # 30%
    exploratory_count = 3     # 10%

    interest_vector = user["interest_vector"]

    # 60% — ChromaDB ANN search using interest vector
    chroma_result = collection.query(
        query_embeddings=[interest_vector.tolist() if hasattr(interest_vector, 'tolist') else interest_vector],
        n_results=personalized_count
    )
    personalized_ids = chroma_result["ids"][0]
    personalized_articles = fetch_articles_by_ids(personalized_ids)

    con = duckdb.connect(DB_PATH, read_only=True)
    try:
        # 30% — latest articles
        fresh_articles = con.execute("""
            SELECT id, title, author, source, word_count, reading_time,
                   published_at, content, scraped_at
            FROM articles_warehouse
            ORDER BY published_at DESC
            LIMIT ?
        """, (fresh_count,)).fetchdf().to_dict(orient="records")

        # collect seen ids to exclude from exploratory
        seen_ids = set(personalized_ids + [a["id"] for a in fresh_articles])

        # 10% — random articles not already in feed
        placeholders = ",".join(["?" for _ in seen_ids])
        exploratory_articles = con.execute(f"""
            SELECT id, title, author, source, word_count, reading_time,
                   published_at, content, scraped_at
            FROM articles_warehouse
            WHERE id NOT IN ({placeholders})
            ORDER BY RANDOM()
            LIMIT ?
        """, list(seen_ids) + [exploratory_count]).fetchdf().to_dict(orient="records")
    finally:
        con.close()

    # merge and deduplicate — personalized first
    combined = personalized_articles + fresh_articles + exploratory_articles
    seen = set()
    feed = []
    for article in combined:
        if article["id"] not in seen:
            seen.add(article["id"])
            feed.append(article)

    return feed


def get_article_by_id(article_id):
    con = duckdb.connect(DB_PATH, read_only=True)
    try:
        result = con.execute("""
            SELECT id, title, author, source, word_count, reading_time,
                   published_at, content, scraped_at
            FROM articles_warehouse
            WHERE id = ?
            LIMIT 1
        """, (article_id,)).fetchdf()
        if result.empty:
            return None
        return result.iloc[0].to_dict()
    finally:
        con.close()