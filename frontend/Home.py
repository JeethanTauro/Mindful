import sys
import os

import requests
import streamlit as st

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from frontend.utils import get_cookies, setup_user, fire_event, fetch_feed, record_article_open, resolve_read_or_bounce

st.set_page_config(page_title="Mindful", page_icon="🧠", layout="wide")

# ── Cookie + User Setup ───────────────────────────────────────────────────────

cookies = get_cookies()
if not cookies.ready():
    st.stop()

user_id, session_id = setup_user(cookies)

# ── Fetch article by ID (for direct URL navigation) ──────────────────────────

def fetch_article_by_id(article_id):
    try:
        response = requests.get(f"http://127.0.0.1:8000/mindful/article/{article_id}")
        data = response.json()
        return data if data else None
    except Exception:
        return None

# ── Header ────────────────────────────────────────────────────────────────────

st.markdown("""
    <h1 style='text-align: center; font-size: 3rem; margin-bottom: 0;'>Mindful</h1>
    <p style='text-align: center; color: gray; font-size: 1.1rem; margin-top: 0;'>
        Your intelligent content feed
    </p>
    <hr/>
""", unsafe_allow_html=True)

# ── Article card renderer ─────────────────────────────────────────────────────

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
        # fire article_open event
        fire_event(user_id, session_id, article["id"], "article_open", "feed")
        # record open time for read/bounce resolution later
        record_article_open(article["id"])
        # store article in session for speed — avoids second db hit
        st.session_state["selected_article"] = dict(article)
        st.query_params["article_id"] = article["id"]
        st.rerun()

# ── Article detail renderer ───────────────────────────────────────────────────

def render_article(article):
    if st.button("← Back to Feed"):
        # resolve read vs bounce based on time spent
        resolve_read_or_bounce(user_id, session_id)
        # clear navigation state
        st.query_params.clear()
        if "selected_article" in st.session_state:
            del st.session_state["selected_article"]
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

# ── Routing ───────────────────────────────────────────────────────────────────

# Priority 1 — URL has article_id (direct link or chatbot redirect)
if "article_id" in st.query_params:
    article_id = st.query_params["article_id"]


    # use session state if available (faster), otherwise fetch from backend
    if "selected_article" in st.session_state and st.session_state["selected_article"]["id"] == article_id:
        article = st.session_state["selected_article"]
    else:
        article = fetch_article_by_id(article_id)
        if article:
            # user navigated directly via URL — fire open event
            fire_event(user_id, session_id, article_id, "article_open", "feed")
            record_article_open(article_id)

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
    articles = fetch_feed(user_id)

    if not articles:
        st.info("No articles found. Run the ingestion pipeline first.")
    else:
        # chunk articles into rows of COLS
        rows = [articles[i:i+COLS] for i in range(0, len(articles), COLS)]
        for row in rows:
            cols = st.columns(COLS)
            for col, article in zip(cols, row):
                with col:
                    render_card(article)