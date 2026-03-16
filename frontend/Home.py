import uuid
from datetime import datetime, timedelta

import streamlit as st
import sys
import os
from streamlit_cookies_manager import EncryptedCookieManager
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from etl.warehouse import con

st.set_page_config(page_title="Mindful", page_icon="🧠", layout="wide")

# ── UUID cookie management ──────────────────────────────────────────────────


cookies = EncryptedCookieManager(prefix="mindful_", password="mindful_secret_key")

if not cookies.ready():
    st.stop()

def get_or_create_uuid():
    user_id = cookies.get("user_id")
    if not user_id:
        user_id = str(uuid.uuid4())
        cookies["user_id"] = user_id
        cookies.save()
    return user_id


user_id = get_or_create_uuid()

# ── Fetch all articles ───────────────────────────────────────────────────────

@st.cache_data(ttl=300)
def fetch_articles(limit=30):
    rows = con.execute("""
        SELECT id, title, author, source, word_count, reading_time, 
               published_at, content, scraped_at
        FROM articles_warehouse
        ORDER BY scraped_at DESC
        LIMIT ?
    """, [limit]).fetchdf()
    return rows

# ── Fetch single article by ID ───────────────────────────────────────────────

def fetch_article_by_id(article_id):
    row = con.execute("""
        SELECT id, title, author, source, word_count, reading_time, 
               published_at, content, scraped_at
        FROM articles_warehouse
        WHERE id = ?
        LIMIT 1
    """, [article_id]).fetchdf()
    if row.empty:
        return None
    return row.iloc[0].to_dict()

# ── Header ───────────────────────────────────────────────────────────────────

st.markdown("""
    <h1 style='text-align: center; font-size: 3rem; margin-bottom: 0;'>Mindful</h1>
    <p style='text-align: center; color: gray; font-size: 1.1rem; margin-top: 0;'>
        Your intelligent content feed
    </p>
    <hr/>
""", unsafe_allow_html=True)

# ── Article cards ────────────────────────────────────────────────────────────

COLS = 3

def render_card(article):
    preview = article["content"][:200].strip() + "..." if article["content"] else ""
    source_tag = article["source"] or "unknown"
    reading_time = f"{article['reading_time']} min read" if article.get("reading_time") else ""

    st.markdown(f"""
        <div style="
            border: 1px solid #2e2e2e;
            border-radius: 12px;
            padding: 1.2rem;
            height: 260px;
            overflow: hidden;
            background-color: #1a1a1a;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            margin-bottom: 1rem;
        ">
            <div>
                <div style="display:flex; gap:8px; margin-bottom:8px; flex-wrap:wrap;">
                    <span style="background:#2a2a2a; color:#aaa; padding:2px 10px; 
                                 border-radius:20px; font-size:0.72rem;">{source_tag}</span>
                </div>
                <p style="font-size:1rem; font-weight:600; margin:0 0 8px 0; 
                          line-height:1.4; color:#f0f0f0;">{article['title']}</p>
                <p style="font-size:0.82rem; color:#888; margin:0; line-height:1.5;">
                    {preview}
                </p>
            </div>
            <div style="font-size:0.75rem; color:#555; margin-top:8px;">
                {reading_time}
            </div>
        </div>
    """, unsafe_allow_html=True)

    if st.button("Read →", key=f"read_{article['id']}"):
        st.query_params["article_id"] = article["id"]   # set URL param
        st.session_state["selected_article"] = article.to_dict()  # keep session for speed
        st.rerun()

# ── Article detail view ──────────────────────────────────────────────────────

def render_article(article):
    if st.button("← Back to Feed"):
        st.query_params.clear()                              # clear URL param
        if "selected_article" in st.session_state:
            del st.session_state["selected_article"]         # clear session state
        st.rerun()

    reading_time = f"{article['reading_time']} min read" if article.get("reading_time") else ""
    author = article.get("author") or "Unknown"

    st.markdown(f"## {article['title']}")
    st.markdown(f"""
        <p style='color:gray; font-size:0.85rem;'>
            {author} · {article['source']} · {reading_time}
        </p>
        <hr/>
    """, unsafe_allow_html=True)
    st.write(article["content"])

# ── Routing logic ─────────────────────────────────────────────────────────────

# Priority 1 — URL has article_id (direct link or chatbot redirect)
if "article_id" in st.query_params:
    article_id = st.query_params["article_id"]

    # use session state if available (faster), otherwise hit DuckDB
    if "selected_article" in st.session_state and st.session_state["selected_article"]["id"] == article_id:
        article = st.session_state["selected_article"]
    else:
        article = fetch_article_by_id(article_id)

    if article:
        render_article(article)
    else:
        st.error("Article not found.")
        st.query_params.clear()

# Priority 2 — session state set (feed card click, already in memory)
elif "selected_article" in st.session_state:
    render_article(st.session_state["selected_article"])

# Priority 3 — no article selected, show feed
else:
    df = fetch_articles()
    rows = [df.iloc[i:i+COLS] for i in range(0, len(df), COLS)]
    for row in rows:
        cols = st.columns(COLS)
        for col, (_, article) in zip(cols, row.iterrows()):
            with col:
                render_card(article)